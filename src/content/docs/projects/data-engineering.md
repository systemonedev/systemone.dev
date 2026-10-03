---
title: 'Data Engineering: Structuring Messy Data'
description: Turning unstructured records into structured fields at pipeline scale, with probability-aware quality gates.
sidebar:
  label: Data Engineering
  order: 2
---

The classic data engineering problem: a table with a free-text column nobody can query. Support
tickets, product descriptions, job titles, transaction memos, scraped listings.

Regex gets you part of the way, plus a maintenance burden. A generative LLM gets you further, at a cost
and speed that make ten million rows impractical. A System One model is built for exactly this shape: a
fixed set of fields, and a probability on each one telling you which rows to trust.

## The pipeline

```text
  source rows ──▶ build state ──▶ ask (concurrently) ──▶ split on probability
                                                              │
                            ┌─────────────────────────────────┼──────────────────┐
                            ▼                                 ▼                  ▼
                       ≥ threshold                        mid band           < floor
                     write the field                    review queue       quarantine
```

## Step 1: Build the state

Quality lives or dies here: see [structured state](/cookbook/structured-state-ingestion/).

```python title="listing_state.py"
STATE_VERSION = "listing-v2"

def listing_state(row) -> dict:
    state = {
        "title": row.title,
        "seller_type": "business" if row.seller_is_business else "individual",
        "image_count": row.image_count,
    }
    # Missing fields are left out, never filled with "(untagged)" or "(empty)": see below.
    if row.price_cents:
        state["price_usd"] = round(row.price_cents / 100, 2)
    if row.seller_category:
        state["seller_tagged_category"] = row.seller_category
    if row.description:
        state["description"] = truncate(row.description, 1200)
    return state
```

An earlier version of this builder wrote `"seller_tagged_category": "(untagged)"` for listings without
a seller category. With `kenning-large-v0.4`, that one placeholder sent an iPhone and a dining table to
`other`. The model reads every value as evidence:
[leave out what you don't know](/cookbook/structured-state-ingestion/#4-leave-out-what-you-dont-know).

## Step 2: Ask every field in one request, many rows concurrently

```python title="questions.py"
from systemone import Choice, Noul

QUESTIONS = {
    "category": Choice("Which category is this listing?", {
        "electronics": None, "clothing": None, "home_garden": "Furniture, decor, tools, garden",
        "vehicles": None, "services": "Work offered, not goods", "other": None,
    }),
    "prohibited": Noul("Does this listing offer something prohibited, such as weapons, drugs or counterfeits?"),
}
AUTO, FLOOR = 0.90, 0.55
```

At pipeline scale the job will fail partway through, so design for resuming from the start:

```python title="pipeline.py"
import asyncio
from systemone import AsyncClient

async def classify_listings(rows_after, checkpoint, batch=512, concurrency=16):
    cursor = checkpoint.read()
    sem = asyncio.Semaphore(concurrency)
    async with AsyncClient("http://localhost:8093", timeout=10) as client:

        async def one(row):
            async with sem:
                return row, await client.system_one(state=listing_state(row), questions=QUESTIONS)

        while rows := rows_after(cursor, limit=batch):
            results = await asyncio.gather(*(one(r) for r in rows))
            write_results(results)
            cursor = rows[-1].id
            checkpoint.write(cursor)          # after the write, never before
            metrics.increment("pipeline.rows", len(results))
```

The checkpoint write must come *after* the result write. The other way round, a crash between the two
silently drops a batch: the worst kind of data bug, because nothing errors.

**Throughput:** a Kenning server answers requests one at a time on its GPU, so plan on roughly 1000 ms
divided by your per-request latency, per GPU: Kenning measured 12–26 items a second on one RTX 3090,
depending on state length. Run more
Kenning replicas, and point the pipeline at them round-robin, to go faster.

## Step 3: Split on probability, and keep it

```python title="write_results.py"
def write_results(results):
    confident, review, quarantine = [], [], []
    for row, r in results:
        c = r.choices["category"]
        p = c.probabilities[c.choice]
        record = {
            "row_id": row.id,
            "category": c.choice,
            "category_probability": p,
            "category_probabilities": c.probabilities,      # keep the full distribution
            "prohibited_probability": r.nouls["prohibited"].noul,
            "model": r.model,
            "state_version": STATE_VERSION,
        }
        (confident if p >= AUTO else review if p >= FLOOR else quarantine).append(record)
        metrics.histogram("pipeline.probability", p, tags={"category": c.choice})

    db.batch_insert("listing_features", confident)
    db.batch_insert("review_queue", review)
    db.batch_insert("quarantine", quarantine)
```

**Store the probability in the warehouse.** This is the part teams regret skipping. Downstream consumers
get to choose their own bar:

```sql
-- A dashboard can be permissive.
SELECT category, count(*) FROM listing_features GROUP BY 1;

-- A billing job can't.
SELECT * FROM listing_features WHERE category_probability >= 0.98;
```

Store the full distribution too. When you later find `electronics` and `home_garden` constantly confused,
the distribution is what tells you, and it can't be recovered without re-running the whole job.

## Step 4: Feed the review queue back

The middle band isn't a dumping ground. It's the most valuable labelled data you'll ever get, because
every row in it is one the model found genuinely hard.

```sql
-- Least certain first: the most information per minute of human attention.
SELECT r.*, l.title, l.description
  FROM review_queue r JOIN listings l ON l.id = r.row_id
 WHERE r.reviewed_at IS NULL
 ORDER BY r.category_probability ASC
 LIMIT 25;
```

Those human labels do two jobs:

- **Calibration check.** Run the [calibration check](/concepts/calibrated-confidence/#verifying-calibration-yourself)
  against them monthly. That's drift detection for free, from work you were already doing.
- **Training data.** Write them as System One training rows (`{state, questions, targets}`, one JSON
  object per line; the format is in the Kenning docs) and fine-tune Kenning on your own data with
  SystemOne Builder. Hard examples are worth far more than easy ones.

## Cost control at scale

Three levers, in order of effect:

**1. Deduplicate before asking.** Real datasets are full of repeats: template listings, copy-pasted
descriptions, bot content. Answers are deterministic, so one answer serves every duplicate:

```python
import hashlib, json
from collections import defaultdict

groups = defaultdict(list)
for row in rows:
    key = hashlib.sha256(json.dumps(listing_state(row), sort_keys=True).encode()).hexdigest()
    groups[key].append(row)
# Ask once per key, then fan the answer out to every row in the group.
```

**2. Filter before asking.** Rows with an empty description and no images don't need a model. Filter them
in SQL.

**3. Process incrementally.** Only new and changed rows, driven by `updated_at`. Full re-runs are for state
or model version changes, and when you do one, write to a new column and compare before cutting over.

## Backfills

Write to a shadow table, compare, then cut over. Never overwrite in place:

```sql
-- Where do the old and new runs disagree, and which is right?
SELECT a.category AS old, b.category AS new, count(*) AS n
  FROM listing_features a
  JOIN listing_features_v3 b USING (row_id)
 WHERE a.category <> b.category
 GROUP BY 1, 2
 ORDER BY n DESC
 LIMIT 20;
```

Check 100 rows from the largest disagreement buckets by hand before cutting over. A change that improves
the average while wrecking one category is easy to ship and hard to notice.

## Next

- [Structured state](/cookbook/structured-state-ingestion/): get step 1 right
- [Moderation & triage](/projects/moderation-triage/): the same shape, with people in the loop
