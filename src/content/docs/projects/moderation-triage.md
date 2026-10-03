---
title: 'Moderation & Triage: Scoring High-Volume Content'
description: A three-tier moderation system where people only see what genuinely needs a person.
sidebar:
  label: Moderation & Triage
  order: 3
---

Content moderation is the classic System One workload: enormous volume, a fixed policy list, a real
cost to being wrong in both directions, and a latency budget measured in the time it takes a post to
appear.

The goal isn't to remove people. It's to make sure the people you have look at the cases where human
judgement actually changes the outcome.

## Architecture

```text
   submission
       │
       ▼
  [ one request: a yes/no question per policy ]   tens of ms, all policies in one pass
       │
       ├── confident violation ────▶ auto-action + appeal path
       ├── confident clean ────────▶ publish
       ├── uncertain ──────────────▶ review queue (priority ordered)
       └── nothing fits ───────────▶ policy-gap triage
```

## One question per policy, one request

Don't fold every policy into one big choice. Separate yes/no questions are separately tunable,
separately measurable and separately thresholded, and they're still answered together in one pass.

```python title="policies.py"
from systemone import Noul

POLICIES = {
    #  name           question                                                        auto-act at
    "harassment":    (Noul("Does this post harass or bully a person?"),                0.97),
    "spam":          (Noul("Is this post spam or unsolicited promotion?"),              0.93),
    "adult":         (Noul("Does this post contain sexual content?"),                   0.96),
    "violence":      (Noul("Does this post threaten violence against someone?"),        0.98),
    "self_harm":     (Noul("Does this post suggest the author may harm themselves?"),   0.85),
    "illegal_goods": (Noul("Does this post offer illegal goods or services?"),          0.96),
}
QUESTIONS = {name: q for name, (q, _) in POLICIES.items()}
```

Look at `self_harm`: a *lower* threshold, because the action it triggers isn't removal. It shows support
resources and routes to a specialist queue. A false positive there is cheap; a false negative isn't.
**The threshold follows the cost of the action, not the severity of the label.** That's the whole reason
per-policy thresholds exist.

```python title="moderate.py"
def moderate(submission) -> dict:
    r = client.system_one(state=submission_state(submission), questions=QUESTIONS)
    return decide({name: r.nouls[name].noul for name in POLICIES}, submission)
```

Six policies, one round trip.

## The decision function

Pure and synchronous, and therefore exhaustively testable:

```python title="decide.py"
CLEAN_AT = 0.05     # every policy at or below this: publish
LEAN_AT = 0.30      # a policy at or above this deserves a look

def decide(p: dict[str, float], submission) -> dict:
    violations = {n: v for n, v in p.items() if v >= POLICIES[n][1]}
    if violations:
        primary = max(violations, key=violations.get)       # act on the strongest; record all
        return {"action": ACTIONS[primary], "policy": primary, "violations": violations,
                "appealable": True, "automated": True}

    if all(v <= CLEAN_AT for v in p.values()):
        return {"action": "publish", "automated": True}

    leaning = {n: v for n, v in p.items() if v >= LEAN_AT}
    if leaning:
        return {"action": "human_review", "priority": priority_for(leaning, submission),
                "leaning": leaning, "automated": False}

    # Nothing is clearly clean and nothing clearly applies: often content your policies don't cover.
    return {"action": "policy_gap_triage", "probabilities": p, "automated": False}
```

## Prioritise the queue by expected harm

A review queue ordered by timestamp wastes your reviewers. Order by how much damage an item does while
it waits:

```python title="priority.py"
import math

HARM_WEIGHT = {"violence": 10, "self_harm": 10, "harassment": 6, "illegal_goods": 5, "adult": 4, "spam": 1}

def priority_for(leaning: dict[str, float], submission) -> float:
    harm = max(HARM_WEIGHT.get(n, 1) * v for n, v in leaning.items())
    # Reach multiplies harm: the same post is worse on an account with 2M followers.
    reach = math.log10(1 + (submission.author.follower_count or 0))
    return harm * (1 + reach)
```

Then pull the highest priority first, with an age term so nothing starves:

```sql
SELECT * FROM review_queue
 WHERE reviewed_at IS NULL
 ORDER BY priority + EXTRACT(EPOCH FROM (now() - created_at)) / 3600 DESC
 LIMIT 25;
```

The age term adds one point of priority per hour waited, which keeps low-priority items from sitting
forever.

## Appeals are part of the system

Any automated action needs a reversal path. This isn't only fairness: **overturned appeals are your
cleanest false-positive measurement**, and they arrive labelled for free.

```python title="appeals.py"
def resolve_appeal(submission_id, upheld: bool, reviewer_id):
    original = db.get_moderation_record(submission_id)
    with db.transaction() as tx:
        tx.record_appeal(submission_id, upheld=upheld, reviewer=reviewer_id)
        if not upheld:
            tx.restore_content(submission_id)
    metrics.increment("moderation.appeal", tags={
        "policy": original.policy,
        "outcome": "upheld" if upheld else "overturned",
        # bucketed, so you can see WHERE in the probability range you're wrong
        "probability_band": band(original.probability),
    })
```

If overturn rates are high in your 0.97–0.99 band, your threshold is too low *or* the model is
overconfident on your content. Both are actionable, and you'd never know without the band tag.

Overturned and upheld appeals, plus reviewer decisions, are also exactly the labelled data that
SystemOne Builder's **Train** page uses to fine-tune and recalibrate Kenning on your content.

## Metrics that tell you it's working

| Metric | Healthy | What it means when it moves |
| :--- | :--- | :--- |
| Auto-action rate | Stable | A spike means an attack or a bad deploy |
| Review queue depth | Flat or falling | Rising: thresholds too strict, or a campaign |
| Appeal overturn rate | Low and stable | Rising: false positives, automate less |
| Policy-gap rate | Low | Rising: a new kind of content your policies miss |
| Probability distribution per policy | Stable | Drifting: recalibrate |
| Time to review, p95 | Within SLA | The number your trust and safety lead is judged on |

Alert hardest on **policy-gap rate**. It's the earliest signal that something new is happening on your
platform, and it shows up there weeks before anywhere else.

## Test the decision logic exhaustively

`decide()` is pure, so being thorough is cheap:

```python title="test_decide.py"
CLEAN = {n: 0.01 for n in POLICIES}

def test_acts_on_a_confident_violation():
    assert decide({**CLEAN, "harassment": 0.99}, SUB)["action"] == ACTIONS["harassment"]

def test_reviews_rather_than_acts_just_below_threshold():
    # The single most important test in the file.
    assert decide({**CLEAN, "harassment": 0.96}, SUB)["action"] == "human_review"

def test_never_publishes_anything_a_policy_leaned_toward():
    for name, (_, auto_at) in POLICIES.items():
        for v in (x / 100 for x in range(6, int(auto_at * 100))):
            assert decide({**CLEAN, name: v}, SUB)["action"] != "publish"
```

## Rolling it out

**Shadow mode, two weeks minimum.** Run alongside your existing process, log what it would have done,
and have moderators compare. You get real thresholds and a real false-positive rate from data instead of
a planning meeting.

**Then automate the confident clean band first.** The safest first step is letting the model *publish*
obviously fine content without review. It shrinks the queue immediately, and the cost of a mistake is a
post a person would have approved anyway.

**Automate removals last,** policy by policy, starting with the one whose overturn rate was lowest in
shadow mode.

## Next

- [Calibrated confidence](/concepts/calibrated-confidence/): set these thresholds properly
- [Data engineering](/projects/data-engineering/): the batch version of this shape
