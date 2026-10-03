---
title: Understanding Calibrated Confidence
description: How to read a System One answer's probabilities, verify they mean what they claim, and pick thresholds from your cost of error.
sidebar:
  label: Calibrated Confidence
  order: 4
---

The probabilities are the whole interface. If they're trustworthy you can automate against them; if
they aren't, everything downstream is theatre. This page is about making sure they're trustworthy.

## What "calibrated" means

A model is **calibrated** if its stated probabilities match observed frequencies:

> Of all the answers a model gives at `0.90`, about 90% should be correct.
> Of those at `0.60`, about 60% should be correct.

That second sentence matters as much as the first. Calibration isn't "usually high confidence." A
model that says `0.60` and is right 60% of the time is *perfectly calibrated*, and far more useful
than one that says `0.95` and is right 80% of the time.

**Accuracy is how often it's right. Calibration is whether it knows when it's right.** You can have
either without the other, and for routing logic calibration is the one you can't do without.

## Reading an answer

Each question type returns a different shape. Know which number to gate on:

```json
{
  "phishing": { "type": "noul", "noul": 0.9045 },
  "kind": {
    "type": "choice", "choice": "phishing", "confidence": 0.7177,
    "probabilities": { "phishing": 0.8118, "spam": 0.1495, "legitimate": 0.0387 }
  },
  "pressure": {
    "type": "score", "score": 1.8091, "confidence": 0.7484,
    "probabilities": { "0": 0.0231, "1": 0.1446, "2": 0.8322 }
  }
}
```

| Question | The probability to gate on | Notes |
| :--- | :--- | :--- |
| `noul` | `noul` itself: P(yes) | There's no `confidence` field: the probability *is* the confidence. P(no) is `1 - noul`. |
| `choice` | `probabilities[choice]`: the winner's probability (0.81 above) | `choice` is just the option with the highest probability. |
| `score` | `probabilities` per level | `score` is the probability-weighted average level: read it with care, see below. |

:::caution[`confidence` is not the winner's probability]
In the System One format, `confidence` is `(max p − 1/n) / (1 − 1/n)`: how far the top answer
stands above an even guess, from 0 (all options equally likely) to 1 (certain). Above, the winner
has probability 0.81 but `confidence` 0.72. Use `confidence` to compare how decisive answers are; put
your **thresholds on probabilities**, because the cost arithmetic below is about the chance of being
right.
:::

### The shape of the distribution tells you *why* it's unsure

Two choice answers with the same winning probability can mean completely different things:

```python
# Contested: two options genuinely compete. Usually a real edge case.
{"phishing": 0.55, "spam": 0.44, "legitimate": 0.01}

# Diffuse: nothing fits. Usually an input your options don't cover.
{"phishing": 0.55, "spam": 0.23, "legitimate": 0.22}
```

The first belongs in a human review queue. The second is telling you your option design has a
hole, and if you see a lot of them, no threshold will save you. Log the full distribution, not just
the winner. You'll want it later.

### A score can hide a split

`score` is an average, and averages hide bimodal distributions:

```python
{"0": 0.48, "1": 0.04, "2": 0.48}   # score = 1.0: "medium"? No: "either none or a lot, I can't tell"
{"0": 0.05, "1": 0.90, "2": 0.05}   # score = 1.0: genuinely medium
```

Both have `score = 1.0`. Before acting on a middle value, check that the probability is actually in
the middle.

## Verifying calibration yourself

Never take calibration on faith on your own data. It takes an afternoon.

**1. Get a labelled sample.** 500–1,000 real production inputs with known correct answers. Use
production inputs, not synthetic ones, and not the model's published benchmark.

**2. Bucket by probability and compare.**

```python title="calibration_check.py"
BUCKETS = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 0.95), (0.95, 1.0001)]

def calibration_report(results):
    """results: [{"p": probability of the predicted answer, "correct": bool}, ...]"""
    rows = []
    for lo, hi in BUCKETS:
        bucket = [r for r in results if lo <= r["p"] < hi]
        if not bucket:
            continue
        claimed = sum(r["p"] for r in bucket) / len(bucket)
        observed = sum(r["correct"] for r in bucket) / len(bucket)
        rows.append({"range": f"{lo}-{min(hi, 1.0)}", "n": len(bucket), "claimed": round(claimed, 3),
                     "observed": round(observed, 3), "gap": round(observed - claimed, 3)})  # negative = overconfident
    return rows
```

For a noul, the predicted answer is "yes" when `noul >= 0.5`, and its probability is
`max(noul, 1 - noul)`.

**3. Read the gap column.** Within a couple of points is healthy. Consistently negative means the
model is overconfident on your data and every threshold you set is optimistic. Raise your thresholds,
recalibrate (SystemOne Builder refits temperatures on labelled data), or stop automating that
question.

**4. Re-run it monthly.** Calibration drifts when your inputs change. That is the real operational
risk: see [drift monitoring](/cookbook/agent-guardrails/#monitoring-that-actually-catches-drift).

SystemOne Builder's Verify page and `systemone bench` compute this for you, along with Brier score and
expected calibration error (ECE), per question.

## Choosing a threshold from cost, not vibes

`0.95` isn't a magic number. People pick it because it sounds responsible. The right threshold falls
out of arithmetic:

```text
Automate when:  P(correct) × value(correct) > P(wrong) × cost(wrong)

i.e.            p × V > (1 − p) × C
                p > C / (V + C)
```

Worked examples:

| Scenario | Cost of error | Value of automating | Threshold |
| :--- | ---: | ---: | ---: |
| Route a support ticket to the wrong queue | 1 | 1 | **0.50** |
| Auto-junk an email | 20 | 1 | **0.95** |
| Block an IP at the firewall | 100 | 1 | **0.99** |
| Auto-delete user content | 500 | 1 | **0.998** |

Units are arbitrary but must be consistent. "One wrong firewall block costs about 100× what one
avoided human review saves" is a judgement your team can actually make and defend.

If the arithmetic demands `0.998` and your model rarely gets there, **that decision isn't
automatable yet.** That's a useful finding, not a failure.

A noul has two thresholds, because both directions can be automated and their costs differ: acting
on a "yes" (`noul >= hi`) and closing on a "no" (`noul <= lo`). Missing a threat is usually far more
expensive than a false alarm, so `lo` is often much stricter than `1 - hi`.

## Three bands, not two

In practice the best-run systems use three:

```python title="three_band_routing.py"
AUTO = 0.95    # from the cost arithmetic above
FLOOR = 0.60   # below this, the model is telling you it has no idea

d = r.choices["route"]
p = d.probabilities[d.choice]
if p >= AUTO:
    apply_automatically(d.choice)
elif p >= FLOOR:
    review_queue.put(item, d, priority="normal")
else:
    # Not a hard case: probably an input your options don't cover.
    triage_queue.put(item, d, reason="below_floor")
    metrics.increment("decisions.below_floor")
```

The bottom band is a design signal, not a workload. If it grows, fix your options.

## Common mistakes

**Comparing probabilities across different option sets.** `0.8` from a two-option question and `0.8`
from a ten-option question aren't the same claim: an even guess is 0.5 in one and 0.1 in the other.

**Averaging probability as a health metric.** Mean probability rising can mean the model got better,
*or* that your input mix got easier. Track the distribution, and accuracy per bucket.

**Treating the threshold as permanent.** Your cost of error changes when the business changes.
Revisit it.

**Forgetting the `other` option.** Without an escape hatch, unfamiliar input gets forced into your
nearest option, often with high probability. See
[what doesn't disappear](/concepts/zero-hallucination/#what-does-not-disappear).

## Next

- [The fuzzy if-statement](/cookbook/fuzzy-if-statement/): thresholds as real code
- [How System One models are trained](/concepts/how-models-are-trained/): where calibration comes from
