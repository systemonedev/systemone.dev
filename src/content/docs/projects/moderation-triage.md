---
title: 'Moderation & Triage: Scoring High-Volume Content'
description: A three-tier moderation system where humans only see what genuinely needs a person.
sidebar:
  label: Moderation & Triage
  order: 3
---

Content moderation is the canonical System 1 workload: enormous volume, a fixed policy
taxonomy, real cost to being wrong in both directions, and a latency budget measured in the
time it takes a post to appear.

The goal is not to remove humans. It is to make sure the humans you have are looking at the
cases where human judgement actually changes the outcome.

## Architecture

```text
   submission
       │
       ▼
  [ multi-policy evaluation ]  ~70ms, all policies in parallel
       │
       ├── confident violation ────▶ auto-action + appeal path
       ├── confident clean ────────▶ publish
       ├── uncertain ──────────────▶ review queue (priority ordered)
       └── below floor ────────────▶ policy-gap triage
```

## One call per policy, in parallel

Resist the urge to ask one model one giant question. Separate policies are separately tunable,
separately measurable, and separately threshold-able — and running them concurrently costs
almost nothing.

```javascript title="policies.js"
export const POLICIES = [
  { name: 'harassment',    categories: ['harassment', 'clean', 'unclear'],           autoAt: 0.97 },
  { name: 'spam',          categories: ['spam', 'clean', 'unclear'],                 autoAt: 0.93 },
  { name: 'adult',         categories: ['adult_content', 'clean', 'unclear'],        autoAt: 0.96 },
  { name: 'violence',      categories: ['violent_threat', 'clean', 'unclear'],       autoAt: 0.98 },
  { name: 'self_harm',     categories: ['self_harm', 'clean', 'unclear'],            autoAt: 0.85 },
  { name: 'illegal_goods', categories: ['illegal_goods', 'clean', 'unclear'],        autoAt: 0.96 },
];
```

Look at `self_harm`: a *lower* auto threshold, because the action it triggers is not removal —
it is surfacing support resources and routing to a specialist queue. A false positive there is
cheap and the false negative is not. **The threshold follows the cost of the action, not the
severity of the label.** That is the whole reason per-policy thresholds exist.

```javascript title="moderate.js"
export async function moderate(submission) {
  const input = serializeSubmission(submission);

  const results = await Promise.all(
    POLICIES.map(async (policy) => ({
      policy,
      decision: await jev.evaluate({ input, categories: policy.categories }),
    })),
  );

  return decide(results, submission);
}
```

Six policies, one round trip's worth of wall time.

## The decision function

Pure, synchronous, and therefore exhaustively testable:

```javascript title="decide.js"
const FLOOR = 0.55;

export function decide(results, submission) {
  const violations = results.filter(
    ({ policy, decision }) =>
      decision.category !== 'clean' &&
      decision.category !== 'unclear' &&
      decision.confidence >= policy.autoAt,
  );

  if (violations.length > 0) {
    // Act on the most confident violation; record all of them.
    const primary = violations.sort(
      (a, b) => b.decision.confidence - a.decision.confidence,
    )[0];

    return {
      action: ACTIONS[primary.policy.name],
      policy: primary.policy.name,
      appealable: true,
      violations,
      automated: true,
    };
  }

  // Anything a policy leaned toward but could not confirm.
  const suspicious = results.filter(
    ({ decision }) =>
      decision.category !== 'clean' && decision.confidence >= FLOOR,
  );

  if (suspicious.length > 0) {
    return {
      action: 'human_review',
      priority: priorityFor(suspicious, submission),
      suspicious,
      automated: false,
    };
  }

  const belowFloor = results.filter((r) => r.decision.confidence < FLOOR);
  if (belowFloor.length === results.length) {
    // Every policy shrugged. Usually content your taxonomy does not cover.
    return { action: 'policy_gap_triage', results, automated: false };
  }

  return { action: 'publish', automated: true };
}
```

## Prioritise the queue by expected harm

A review queue ordered by timestamp wastes your reviewers. Order by how much damage the item
does while it waits:

```javascript title="priority.js"
const HARM_WEIGHT = {
  violence: 10, self_harm: 10, harassment: 6,
  adult: 4, illegal_goods: 5, spam: 1,
};

export function priorityFor(suspicious, submission) {
  const harm = Math.max(
    ...suspicious.map(
      ({ policy, decision }) => (HARM_WEIGHT[policy.name] ?? 1) * decision.confidence,
    ),
  );

  // Reach multiplies harm: the same post is worse on an account with 2M followers.
  const reach = Math.log10(1 + (submission.author.followerCount ?? 0));

  return harm * (1 + reach);
}
```

Then pull highest-priority first, with an age-based floor so nothing starves:

```javascript
const batch = await db.query(`
  SELECT * FROM review_queue
   WHERE reviewed_at IS NULL
   ORDER BY (priority + EXTRACT(EPOCH FROM (now() - created_at)) / 3600) DESC
   LIMIT $1
`, [25]);
```

The age term converts to "one point of priority per hour waited," which keeps low-priority items
from sitting forever.

## Appeals are part of the system

Any automated action needs a reversal path. This is not only fairness — **overturned appeals are
your cleanest false-positive measurement**, and they arrive labelled for free.

```javascript title="appeals.js"
export async function resolveAppeal({ submissionId, upheld, reviewerId }) {
  const original = await db.getModerationRecord(submissionId);

  await db.transaction(async (tx) => {
    await tx.recordAppeal({ submissionId, upheld, reviewerId });
    if (!upheld) await tx.restoreContent(submissionId);
  });

  metrics.increment('moderation.appeal', {
    policy: original.policy,
    outcome: upheld ? 'upheld' : 'overturned',
    // Bucketed so you can see WHERE in the confidence range you are wrong.
    confidence_band: band(original.confidence),
  });
}
```

If overturn rates are high in your 0.97–0.99 band, your threshold is too low *or* your model is
overconfident on your distribution. Both are actionable, and you would not have known without
the band tag.

## Metrics that tell you it is working

| Metric | Healthy | What it means when it moves |
| :--- | :--- | :--- |
| Auto-action rate | Stable | A spike means an attack or a bad deploy |
| Review queue depth | Flat or falling | Rising = thresholds too tight, or a campaign |
| Appeal overturn rate | Low and stable | Rising = false positives, lower your automation |
| `unclear` / policy-gap rate | Low | Rising = new content type your policies miss |
| Mean confidence per policy | Stable | Drifting = recalibrate |
| Time-to-review, p95 | Within SLA | The number your trust & safety lead is judged on |

The one to alert on hardest is **policy-gap rate**. It is the earliest signal that something new
is happening on your platform, and it shows up there weeks before it shows up anywhere else.

## Test the decision logic exhaustively

`decide()` is pure, so you can be thorough cheaply:

```javascript title="decide.test.js"
const r = (name, category, confidence) => ({
  policy: POLICIES.find((p) => p.name === name),
  decision: { category, confidence },
});

it('auto-actions a confident violation', () => {
  expect(decide([r('harassment', 'harassment', 0.99)], sub).action)
    .toBe(ACTIONS.harassment);
});

it('reviews rather than acts just below threshold', () => {
  // The single most important test in the file.
  expect(decide([r('harassment', 'harassment', 0.96)], sub).action)
    .toBe('human_review');
});

it('flags a policy gap when everything is below the floor', () => {
  const all = POLICIES.map((p) => r(p.name, 'unclear', 0.3));
  expect(decide(all, sub).action).toBe('policy_gap_triage');
});

it('never publishes anything a policy leaned toward', () => {
  for (const p of POLICIES) {
    for (let c = FLOOR; c < p.autoAt; c += 0.01) {
      const violationLabel = p.categories[0];
      expect(decide([r(p.name, violationLabel, c)], sub).action).not.toBe('publish');
    }
  }
});
```

## Rolling it out

**Shadow mode, two weeks minimum.** Run alongside your existing process, log what it would have
done, and have moderators compare. You get your real thresholds and your real false-positive
rate from data instead of from a planning meeting.

**Then automate the confident clean band first.** The safest possible first step is letting the
model *publish* obviously fine content without review — it reduces queue depth immediately and
the cost of being wrong is a post that a human would have approved anyway.

**Automate removals last,** policy by policy, starting with the one whose appeal overturn rate
is lowest in shadow.

## Next

- [Calibrated Confidence](/concepts/calibrated-confidence/) — set these thresholds properly
- [Data Engineering](/projects/data-engineering/) — the batch version of this shape
