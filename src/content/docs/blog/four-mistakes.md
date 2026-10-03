---
title: The Four Mistakes Every System One Codebase Makes First
description: Uncertainty folded into the wrong branch, thresholds from vibes, no escape option, and no drift monitoring.
date: 2026-10-03T12:00:00Z
authors:
  - maintainers
excerpt: The same four bugs show up in almost every System One integration. All four are cheap to fix on day one and expensive to fix in month six.
tags: [patterns, production]
---

Four bugs show up over and over in System One integrations. They aren't subtle once you know to look,
and all four are cheap to fix at the start and painful to fix once six months of data has been written
under them.

## 1. Folding uncertainty into the wrong branch

The most common, and the only one on this list that's a straightforward correctness bug:

```python
# The bug.
if r.nouls["fraud"].noul > 0.95:
    block_transaction()
else:
    allow_transaction()
```

A fraud probability of `0.94`, the model saying *"this is very probably fraud"*, falls through to
`allow_transaction()`.

The `else` branch has silently become a bucket for two opposite situations: "confidently fine" and
"alarmingly uncertain". In your logs, the second is now indistinguishable from the first.

```python
# The fix: uncertainty is its own outcome, with a threshold on each side.
p = r.nouls["fraud"].noul
if p >= 0.95:
    block_transaction()
elif p <= 0.02:
    allow_transaction()
else:
    manual_review(transaction, p)
```

**Rule: a yes/no answer needs two thresholds, and the middle is a real outcome.** More in
[the fuzzy if-statement](/cookbook/fuzzy-if-statement/#the-ordering-mistake).

A close cousin: gating on a choice's `confidence` field. In the System One format, `confidence`
measures how far the winner stands above an even guess. It isn't the winner's probability. Gate on
`probabilities[choice]` ([why](/concepts/calibrated-confidence/#reading-an-answer)).

## 2. Thresholds chosen because they sound responsible

`0.95` appears in almost every codebase, and almost nobody can say why. It isn't derived from anything.
It just sounds careful.

The actual arithmetic is one line:

```text
automate when   p > cost_of_error / (value_of_automating + cost_of_error)
```

Which gives very different numbers depending on what the decision *does*:

| Action | Cost of being wrong | Threshold |
| :--- | ---: | ---: |
| Route a ticket to the wrong queue | 1 | **0.50** |
| Auto-junk an email | 20 | **0.95** |
| Block an IP | 100 | **0.99** |
| Delete user content | 500 | **0.998** |

Two useful consequences. First, plenty of low-stakes decisions should be automated at `0.6`: teams leave
easy wins on the table with a blanket 0.95. Second, if the arithmetic demands `0.998` and your model
rarely gets there, **that decision isn't automatable yet**, and knowing that is worth more than a
threshold that pretends otherwise.

## 3. No escape option

```python
Choice("Which team?", {"billing": None, "technical": None, "account": None})
```

The model has to return one of these. When a message is none of them (a legal threat, a partnership
enquiry, a language you don't support) it returns the nearest one. Often with high probability, because
relative to the other two options it really is the best fit.

Your probability safety net doesn't catch this. The number is high. The answer is wrong.

```python
Choice("Which team?", {"billing": None, "technical": None, "account": None,
                       "other": "Anything that fits none of the above"})
```

Then alert on `other` as a share of traffic. A rising `other` rate is the earliest signal that your
options have drifted out of date: it moves weeks before accuracy visibly degrades.

## 4. Monitoring uptime instead of the distribution

Almost everyone monitors request count, error rate and p99 latency. Almost nobody monitors the thing
that actually fails.

System One models degrade *silently*. Calibration drifts when your inputs shift: a new market, a new
product surface, an adversary adapting. The model keeps returning well-formed answers with plausible
probabilities. Your dashboards stay green. The answers get worse.

Four signals worth alerting on:

```python
metrics.histogram("decision.probability", p, tags={"choice": d.choice})
metrics.increment("decision.choice", tags={"choice": d.choice})
metrics.increment("decision.below_floor")
metrics.increment("decision.degraded")        # fallbacks taken
```

| Signal | What a move means |
| :--- | :--- |
| Winning probability falling | Your inputs shifted: re-check calibration |
| Answer mix shifting | Either the world changed, or your state builder did |
| `below_floor` rate rising | Real inputs your options don't cover |
| `degraded` rate above zero | You're silently running on fallbacks |

That last one deserves its own alert. A timeout fallback that quietly allows every request, while the
error rate stays at zero because you handled the exception, is the failure that does the most damage
before anyone notices.

Beyond metrics, **sample and read the decisions**: fifty a week, by hand. Every team that has been
burned here says the same thing afterwards: the dashboards looked fine.

## The pattern behind all four

Each of these is the same mistake in a different costume: **treating the probability as decoration
instead of as the primary output.**

If you take one thing away, make it this. The chosen option is just the most likely one. The
probabilities behind it are what make the model safe to build on. Code that ignores them has thrown away
the only thing that separates a decision model from a very fast guess.

---

Further reading: [Understanding calibrated confidence](/concepts/calibrated-confidence/) and
[The fuzzy if-statement](/cookbook/fuzzy-if-statement/).
