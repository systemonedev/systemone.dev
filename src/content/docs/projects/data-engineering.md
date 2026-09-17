---
title: 'Data Engineering: Map-Reducing Messy Data'
description: Turning unstructured records into structured features at pipeline scale, with confidence-aware quality gates.
sidebar:
  label: Data Engineering
  order: 2
---

The classic data engineering problem: a table with a free-text column that nobody can query.
Support tickets, product descriptions, job titles, transaction memos, scraped listings.

Regex gets you 60% and a maintenance burden. An LLM gets you 90% and a bill that makes the
project non-viable at ten million rows. A decision model is built for exactly this shape.

## The pipeline

```text
  source rows ──▶ serialize ──▶ batch evaluate ──▶ confidence split
                                                        │
                            ┌───────────────────────────┼──────────────────┐
                            ▼                           ▼                  ▼
                    ≥ threshold                     mid band           < floor
                    write feature                 review queue      quarantine
```

## Step 1: Serialize the row

Classification quality lives or dies here — see
[Structured State Ingestion](/cookbook/structured-state-ingestion/).

```javascript title="serialize.js"
export const SERIALIZER_VERSION = 'listing-v2';

export function serializeListing(row) {
  return [
    `Title: ${row.title}`,
    `Price: ${row.price_cents ? `$${(row.price_cents / 100).toFixed(2)}` : 'not listed'}`,
    `Seller type: ${row.seller_is_business ? 'business' : 'individual'}`,
    `Category as tagged by seller: ${row.seller_category ?? '(untagged)'}`,
    `Has images: ${row.image_count > 0} (${row.image_count})`,
    '',
    'Description:',
    truncate(row.description ?? '(empty)', 1500),
  ].join('\n');
}
```

## Step 2: Batch with checkpointing

At pipeline scale, the job will fail partway through. Design for resumption from the start.

```javascript title="pipeline.js"
const BATCH_SIZE = 256;
const CONCURRENCY = 8;

const CATEGORIES = [
  'electronics', 'clothing', 'home_garden', 'vehicles',
  'services', 'prohibited', 'other',
];

const AUTO = 0.90;
const FLOOR = 0.55;

export async function classifyListings({ since, checkpoint }) {
  let cursor = await checkpoint.read();
  let processed = 0;

  for await (const batch of streamRows({ since, after: cursor, size: BATCH_SIZE * CONCURRENCY })) {
    const chunks = chunk(batch, BATCH_SIZE);

    const results = (
      await Promise.all(
        chunks.map(async (rows) => {
          const decisions = await jev.evaluateBatch({
            inputs: rows.map(serializeListing),
            categories: CATEGORIES,
          });
          return rows.map((row, i) => ({ row, decision: decisions[i] }));
        }),
      )
    ).flat();

    await writeResults(results);

    cursor = batch.at(-1).id;
    await checkpoint.write(cursor);   // after the write, never before
    processed += results.length;

    metrics.increment('pipeline.rows', results.length);
  }

  return { processed, cursor };
}
```

The checkpoint write must come *after* the result write. Reversed, a crash between the two
silently drops a batch — the worst kind of data bug, because nothing errors.

## Step 3: Split on confidence

```javascript title="write-results.js"
async function writeResults(results) {
  const confident = [];
  const review = [];
  const quarantine = [];

  for (const { row, decision } of results) {
    const record = {
      row_id: row.id,
      category: decision.category,
      confidence: decision.confidence,
      scores: decision.scores,               // keep the full distribution
      serializer_version: SERIALIZER_VERSION,
      classified_at: new Date().toISOString(),
    };

    if (decision.confidence >= AUTO) confident.push(record);
    else if (decision.confidence >= FLOOR) review.push(record);
    else quarantine.push(record);

    metrics.histogram('pipeline.confidence', decision.confidence, {
      category: decision.category,
    });
  }

  await Promise.all([
    db.batchInsert('listing_features', confident),
    db.batchInsert('review_queue', review),
    db.batchInsert('quarantine', quarantine),
  ]);
}
```

**Store the confidence in the warehouse.** This is the part teams regret skipping. Downstream
consumers get to choose their own bar:

```sql
-- A dashboard can be permissive.
SELECT category, count(*) FROM listing_features GROUP BY 1;

-- A billing job cannot.
SELECT * FROM listing_features WHERE confidence >= 0.98;
```

Store `scores` too. When you later discover `electronics` and `home_garden` are constantly
confused, the full distribution is what tells you — and it is not recoverable after the fact
without re-running the whole job.

## Step 4: Feed the review queue back

The mid-confidence band is not just a dumping ground. It is the highest-value labelled data you
will ever get, because every row in it is one the model found genuinely hard.

```javascript title="review.js"
export async function nextForReview(reviewerId, limit = 25) {
  // Least confident first — most information gained per minute of human attention.
  return db.query(
    `SELECT r.*, l.title, l.description
       FROM review_queue r
       JOIN listings l ON l.id = r.row_id
      WHERE r.reviewed_at IS NULL
      ORDER BY r.confidence ASC
      LIMIT $1`,
    [limit],
  );
}

export async function submitReview({ rowId, correctCategory, reviewerId }) {
  await db.transaction(async (tx) => {
    await tx.query(
      `UPDATE review_queue
          SET reviewed_at = now(), reviewer_id = $2, corrected_category = $3
        WHERE row_id = $1`,
      [rowId, reviewerId, correctCategory],
    );

    await tx.query(
      `INSERT INTO listing_features (row_id, category, confidence, source)
       VALUES ($1, $2, 1.0, 'human')
       ON CONFLICT (row_id) DO UPDATE
         SET category = EXCLUDED.category, confidence = 1.0, source = 'human'`,
      [rowId, correctCategory],
    );
  });
}
```

Those human labels are your calibration set. Run the
[calibration check](/concepts/calibrated-confidence/#verifying-calibration-yourself) against them
monthly — you get drift detection for free from work you were already doing.

## Cost control at scale

Three levers, in order of effect:

**1. Deduplicate before classifying.** Real datasets are full of repeats — template listings,
copy-pasted descriptions, bot-generated content. Hash first:

```javascript
const byHash = new Map();
for (const row of rows) {
  const h = sha256(serializeListing(row));
  (byHash.get(h) ?? byHash.set(h, []).get(h)).push(row);
}

const decisions = await jev.evaluateBatch({
  inputs: [...byHash.keys()].map((h) => inputFor(h)),
  categories: CATEGORIES,
});
// Fan the decision back out to every row sharing the hash.
```

On listing and review data this alone routinely cuts volume by a third or more.

**2. Gate cheaply before deciding expensively.** Rows with an empty description and no images do
not need a model. Filter them in SQL.

**3. Classify incrementally.** Only new and changed rows, driven by `updated_at`. Full
reclassification is for serializer or model version changes — and when you do it, write to a new
column and compare before cutting over.

## Backfills

```javascript title="backfill.js"
// Write to a shadow column, compare, then cut over. Never classify in place.
await classifyListings({
  since: '1970-01-01',
  target: 'listing_features_v3',
  checkpoint: fileCheckpoint('.backfill-v3.cursor'),
});

// Where do old and new disagree, and which is right?
const drift = await db.query(`
  SELECT a.category AS old, b.category AS new, count(*) AS n
    FROM listing_features a
    JOIN listing_features_v3 b USING (row_id)
   WHERE a.category <> b.category
   GROUP BY 1, 2
   ORDER BY n DESC
   LIMIT 20
`);
```

Sample 100 rows from the largest disagreement buckets and check them by hand before cutting
over. A serializer change that improves the average while destroying one category is easy to
ship and hard to notice.

## Next

- [Structured State Ingestion](/cookbook/structured-state-ingestion/) — get step 1 right
- [Moderation & Triage](/projects/moderation-triage/) — the same shape, with humans in the loop
