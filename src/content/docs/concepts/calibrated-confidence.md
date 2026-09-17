---
title: Understanding Calibrated Confidence
description: How to read a probability score, verify it means what it claims, and pick thresholds from your cost of error.
sidebar:
  label: Calibrated Confidence
  order: 4
---

Confidence is the whole interface. If the number is trustworthy you can automate against it; if
it is not, everything downstream is theatre. This page is about making sure it is trustworthy.

## What "calibrated" means

A model is **calibrated** if its stated probabilities match observed frequencies:

> Of all the decisions a model returns at confidence `0.90`, about 90% should be correct.
> Of those at `0.60`, about 60% should be correct.

That second sentence matters as much as the first. Calibration is not "usually high
confidence." A model that says `0.60` and is right 60% of the time is *perfectly calibrated* —
and far more useful than one that says `0.95` and is right 80% of the time.

**Accuracy is how often it is right. Calibration is whether it knows.** You can have either
without the other, and for routing logic, calibration is the one you cannot do without.

## Reading a full response

Most decision models return more than the winning label. Use all of it:

```json
{
  "category": "phishing",
  "confidence": 0.97,
  "scores": {
    "phishing": 0.97,
    "spam": 0.021,
    "legitimate": 0.009
  },
  "latency_ms": 71
}
```

- **`confidence`** — the probability of the top category. Your automation gate.
- **`scores`** — the full distribution. This is where the diagnostics are.
- **`category`** — just `argmax(scores)`. It carries no information the distribution doesn't.

### The shape of the distribution tells you *why* it is unsure

Two responses with identical `confidence: 0.55` can mean completely different things:

```javascript
// Contested: two categories genuinely compete. Usually a real edge case.
{ phishing: 0.55, spam: 0.44, legitimate: 0.01 }

// Diffuse: nothing fits. Usually an input your categories don't cover.
{ phishing: 0.55, spam: 0.23, legitimate: 0.22 }
```

The first belongs in a human review queue. The second is telling you your category design has a
hole — and if you see a lot of them, no threshold will save you. Log the full distribution, not
just the top score. You will want it later.

## Verifying calibration yourself

Never take calibration on faith on your own data. It takes an afternoon.

**1. Get a labelled sample.** 500–1,000 real production inputs with known correct answers.
Production inputs — not synthetic ones, not the vendor's benchmark.

**2. Bucket by confidence and compare.**

```javascript title="calibration-check.js"
const BUCKETS = [
  [0.5, 0.6], [0.6, 0.7], [0.7, 0.8],
  [0.8, 0.9], [0.9, 0.95], [0.95, 1.0],
];

function calibrationReport(results) {
  return BUCKETS.map(([lo, hi]) => {
    const inBucket = results.filter(
      (r) => r.confidence >= lo && r.confidence < hi,
    );
    if (inBucket.length === 0) return { range: `${lo}-${hi}`, n: 0 };

    const correct = inBucket.filter((r) => r.predicted === r.actual).length;
    const observed = correct / inBucket.length;
    const claimed =
      inBucket.reduce((s, r) => s + r.confidence, 0) / inBucket.length;

    return {
      range: `${lo}-${hi}`,
      n: inBucket.length,
      claimed: claimed.toFixed(3),
      observed: observed.toFixed(3),
      gap: (observed - claimed).toFixed(3), // negative = overconfident
    };
  });
}
```

**3. Read the gap column.** Within a couple of points is healthy. Consistently negative means
the model is overconfident on your data and every threshold you set is optimistic. Shift your
thresholds up, or stop automating that category.

**4. Re-run it monthly.** Calibration drifts. That is the actual operational risk — see
[drift monitoring](/cookbook/agent-guardrails/#monitoring-that-actually-catches-drift).

## Choosing a threshold from cost, not vibes

`0.95` is not a magic number. It is a number people pick because it sounds responsible. The
right threshold falls out of arithmetic:

```text
Automate when:  P(correct) × value(correct) > P(wrong) × cost(wrong)

i.e.            c × V > (1 - c) × C
                c > C / (V + C)
```

Worked examples:

| Scenario | Cost of error | Value of automating | Threshold |
| :--- | ---: | ---: | ---: |
| Route a support ticket to the wrong queue | 1 | 1 | **0.50** |
| Auto-junk an email | 20 | 1 | **0.95** |
| Block an IP at the firewall | 100 | 1 | **0.99** |
| Auto-delete user content | 500 | 1 | **0.998** |

Units are arbitrary but must be consistent — "one wrong firewall block costs about 100× what
one avoided human review saves" is a judgement your team can actually make and defend.

If the arithmetic demands `0.998` and your model rarely exceeds `0.97`, **that decision is not
automatable yet.** That is a useful finding, not a failure.

## Three bands, not two

In practice the best-run systems use three:

```javascript title="three-band-routing.js"
const AUTO = 0.95;   // from the cost arithmetic above
const FLOOR = 0.60;  // below this, the model is telling you it has no idea

if (decision.confidence >= AUTO) {
  await applyAutomatically(decision.category);
} else if (decision.confidence >= FLOOR) {
  await humanReviewQueue.push({ item, decision, priority: 'normal' });
} else {
  // Not a hard case — probably an input your categories don't cover.
  await triageQueue.push({ item, decision, reason: 'below_floor' });
  metrics.increment('decisions.below_floor');
}
```

The bottom band is a design signal, not a workload. If it grows, fix your categories.

## Common mistakes

**Comparing confidence across different category sets.** `0.8` from a 2-category call and `0.8`
from a 10-category call are not the same claim. Random chance is 0.5 in one and 0.1 in the other.

**Averaging confidence as a health metric.** Mean confidence rising can mean the model got
better *or* that your input mix got easier. Track the *distribution* and accuracy-per-bucket.

**Treating the threshold as permanent.** Your cost of error changes when the business changes.
Revisit it.

**Forgetting the `other` category.** Without an escape hatch, unfamiliar input gets forced into
your nearest label — often with high confidence. See
[Zero Hallucination](/concepts/zero-hallucination/#what-does-not-disappear).

## Next

- [The fuzzy if-statement](/cookbook/fuzzy-if-statement/) — thresholds as real code
- [RLCD vs. RLHF](/concepts/rlcd-vs-rlhf/) — where calibration comes from
