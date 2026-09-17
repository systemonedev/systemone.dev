---
title: The Four Mistakes Every System 1 Codebase Makes First
description: Confidence checks in the wrong place, thresholds from vibes, no escape category, and no drift monitoring.
date: 2026-09-14T12:00:00Z
authors:
  - maintainers
excerpt: Reviewing decision-native integrations, the same four bugs show up almost every time. All four are cheap to fix on day one and expensive to fix in month six.
tags: [patterns, production]
---

Reviewing decision-native integrations, four bugs show up over and over. They are not subtle
once you know to look, and all four are cheap to fix at the start and painful to fix once
you have six months of data written under them.

## 1. Gating on confidence in the wrong place

The most common, and the only one on this list that is a straightforward correctness bug:

```javascript
// The bug.
if (decision.category === 'fraud' && decision.confidence > 0.95) {
  blockTransaction();
} else {
  allowTransaction();
}
```

A decision of `{ category: 'fraud', confidence: 0.94 }` — the model saying *"this is very
probably fraud"* — falls through to `allowTransaction()`.

The `else` branch has silently become a bucket for two opposite situations: "confidently fine"
and "alarmingly uncertain." The second one is now indistinguishable from the first in your logs.

```javascript
// The fix: uncertainty is its own outcome, checked first.
if (decision.confidence < 0.95) return manualReview(transaction, decision);
return decision.category === 'fraud' ? blockTransaction() : allowTransaction();
```

**Rule: gate on confidence, then branch on category.** Never the reverse, never combined in one
condition. More on this in
[the fuzzy if-statement](/cookbook/fuzzy-if-statement/#the-ordering-mistake).

## 2. Thresholds chosen because they sound responsible

`0.95` appears in almost every codebase, and almost nobody can say why. It is not derived from
anything. It sounds careful.

The actual arithmetic is one line:

```text
automate when   confidence > cost_of_error / (value_of_automating + cost_of_error)
```

Which gives very different numbers depending on what the decision *does*:

| Action | Cost of being wrong | Threshold |
| :--- | ---: | ---: |
| Route a ticket to the wrong queue | 1 | **0.50** |
| Auto-junk an email | 20 | **0.95** |
| Block an IP | 100 | **0.99** |
| Delete user content | 500 | **0.998** |

Two useful consequences. First, plenty of low-stakes decisions should be automated at `0.6` —
teams routinely leave easy wins on the table by applying a blanket 0.95. Second, if the
arithmetic demands `0.998` and your model tops out at `0.97`, **that decision is not automatable
yet**, and knowing that is worth more than a threshold that pretends otherwise.

## 3. No escape category

```javascript
categories: ['billing', 'technical', 'account']
```

The model must return one of these. When a message arrives that is none of them — a legal
threat, a partnership enquiry, a language you do not support — it returns the nearest one. Often
with high confidence, because relative to the other two options it really is the best fit.

Your confidence-based safety net does not catch this. The number is high. The answer is wrong.

```javascript
categories: ['billing', 'technical', 'account', 'other']
```

Then alert on `other` as a share of traffic. A rising `other` rate is the earliest signal your
taxonomy has drifted out of date — it moves weeks before accuracy visibly degrades.

## 4. Monitoring uptime instead of distribution

Almost everyone monitors: request count, error rate, p99 latency. Almost nobody monitors the
thing that actually fails.

Decision models degrade *silently*. Calibration drifts when your input distribution shifts — a
new market, a new product surface, an adversary adapting. The model keeps returning
well-formed, structurally valid, confidently-scored answers. Your dashboards stay green. The
answers get worse.

Four signals worth alerting on:

```javascript
metrics.histogram('decision.confidence', decision.confidence, { category: decision.category });
metrics.increment('decision.category', { category: decision.category });
metrics.increment('decision.below_floor');
metrics.increment('decision.degraded');   // fallbacks taken
```

| Signal | What a move means |
| :--- | :--- |
| Mean confidence falling | Input distribution shifted — re-verify calibration |
| Category mix shifting | Either the world changed or your serializer did |
| `below_floor` rate rising | Real inputs your categories do not cover |
| `degraded` rate above zero | You are silently running on fallbacks |

That last one deserves its own alert. A timeout fallback that quietly returns `allow` on every
request, while error rate stays at zero because you handled the exception, is the failure mode
that does the most damage before anyone notices.

And beyond metrics: **sample and read the decisions.** Fifty a week, by hand. Every team that
has been burned here says the same sentence afterwards — the dashboards looked fine.

## The pattern behind all four

Each of these is the same mistake in a different costume: **treating the confidence score as
decoration rather than as the primary output.**

If you internalise one thing, make it this. The category is just `argmax`. The confidence — and
the full distribution behind it — is what makes the model safe to build on. Code that ignores it
is code that has thrown away the only thing distinguishing a decision model from a very fast
guess.

---

Further reading: [Understanding Calibrated Confidence](/concepts/calibrated-confidence/) and
[The Fuzzy If-Statement](/cookbook/fuzzy-if-statement/).
