---
title: The "Fuzzy" If-Statement
description: Routing logic built on probability bands, the foundational System One code pattern.
sidebar:
  label: The Fuzzy If-Statement
  order: 1
---

Every System One integration is, at bottom, one pattern: a typed answer, a probability gate, and a
branch. Get the shape right once and every later integration is a variation.

## The pattern

```python title="fuzzy_if.py"
from systemone import Client, Choice

client = Client("http://localhost:8093")
r = client.system_one(state=application, questions={
    "decision": Choice("What should happen to this application?",
                       {"approve": None, "reject": None, "review": None}),
})
d = r.choices["decision"]

# 1. Gate on the winner's probability FIRST.
if d.probabilities[d.choice] < THRESHOLD:
    return escalate(application, d)

# 2. Then branch on the answer.
match d.choice:
    case "approve": return approve()
    case "reject":  return reject()
    case "review":  return queue_for_review()
```

## The ordering mistake

This is the most common bug in new System One code:

```python title="wrong.py"
# WRONG: the uncertainty is folded into the "allow" branch.
if r.nouls["fraud"].noul > 0.95:
    block_transaction()
else:
    allow_transaction()     # a 0.94 fraud signal silently becomes "allow"
```

A fraud probability of `0.94`, a strong signal, falls into `else` and gets approved. The `else`
branch has quietly become a dumping ground for *both* "confidently fine" and "alarmingly uncertain",
which are opposite situations.

```python title="right.py"
# RIGHT: uncertainty is its own branch, with a threshold on each side.
p = r.nouls["fraud"].noul
if p >= 0.95:
    block_transaction()
elif p <= 0.02:
    allow_transaction()
else:
    manual_review(transaction, p)          # 0.94 lands here
```

**Rule: uncertainty is a first-class outcome, not a modifier on another outcome.** A noul needs two
thresholds: one to act on yes, one to act on no.

## Three bands

Two bands (automate or escalate) is the minimum. Three is better, because "uncertain" and "nothing
fits" need different handling:

```python title="three_band.py"
AUTO = 0.95    # derived from your cost of error: see /concepts/calibrated-confidence/
FLOOR = 0.60   # below this the model is signalling "none of these fit well"

def route(item):
    r = client.system_one(state=item, questions={"route": Choice("Where should this go?", OPTIONS)})
    d = r.choices["route"]
    p = d.probabilities[d.choice]
    metrics.histogram("decision.probability", p, tags={"choice": d.choice})

    if p >= AUTO:
        return {"action": ACTIONS[d.choice], "automated": True, "answer": d}
    if p >= FLOOR:
        return {"action": "human_review", "automated": False, "answer": d}
    # Not a hard case: probably an input your options don't cover.
    metrics.increment("decision.below_floor", tags={"choice": d.choice})
    return {"action": "triage", "automated": False, "answer": d, "reason": "below_floor"}
```

## Per-answer thresholds

Cost of error is rarely uniform. Wrongly approving a refund isn't the same as wrongly denying one.
Encode that:

```python title="thresholds.py"
# Asymmetric by design: destructive actions need more certainty than safe ones.
THRESHOLDS = {
    "block": 0.99,        # a false positive blocks a legitimate user
    "quarantine": 0.95,
    "flag": 0.85,
    "allow": 0.80,        # the safe default; a mistake here costs little
}
DEFAULT_THRESHOLD = 0.95

def is_automatable(d) -> bool:
    return d.probabilities[d.choice] >= THRESHOLDS.get(d.choice, DEFAULT_THRESHOLD)
```

Keep these in config, not scattered through the codebase. You'll tune them, and you want the diff to
be one file.

## Always include an escape option

If reality contains a case your list doesn't, the model still has to pick one of yours, often with
misleadingly high probability. Give it somewhere to go:

```python
OPTIONS = {
    "billing_question": "Charges, refunds, invoices",
    "technical_issue": "Bugs, errors, outages",
    "account_access": "Logins, passwords, permissions",
    "other": "Anything that fits none of the above",   # the escape hatch
}
```

Then alert on its share of traffic. A rising `other` rate is the earliest signal that your options
have drifted out of date, long before accuracy visibly drops.

## Ask everything at once

With a generative model you'd chain calls: is it relevant? then what's the intent? With System One, ask
every question in **one** request. They're answered in the same pass over the state, so two questions
cost about the same as one. On Kenning (one RTX 3090), the request below takes 38 ms with both
questions, 38 ms with one, and 76 ms as two separate requests:

```python title="pipeline.py"
def handle_message(msg):
    r = client.system_one(state={"message": msg.text, "channel": msg.channel}, questions={
        "actionable": Noul("Does this message ask us to do something?"),
        "intent": Choice("What does the sender want?", {
            "refund": "Money back for a charge",
            "bug_report": "Something is broken",
            "feature_request": "Something new",
            "other": None,
        }),
    })
    if r.nouls["actionable"].noul <= 0.05:
        return {"action": "drop"}

    intent = r.choices["intent"]
    if intent.probabilities[intent.choice] < 0.9:
        return {"action": "human_review", "intent": intent}

    # The expensive generative path, now taken rarely (seconds).
    if intent.choice == "bug_report":
        return {"action": "draft_reply", "body": llm.chat(msg.text)}
    return {"action": ROUTES[intent.choice]}
```

One fast call that prevents a slow one is a good trade almost every time.

## Testing it

The nice property of this pattern: your routing logic is deterministic and testable in isolation.
Test the routing with fixtures, and evaluate the model separately.

```python title="test_route.py"
from systemone import NoulAnswer
from route import decide          # decide(fraud: NoulAnswer) -> str, no model call inside

def test_automates_above_the_threshold():
    assert decide(NoulAnswer(0.99)) == "block"

def test_escalates_a_strong_but_uncertain_signal():
    # The regression test for the ordering bug above.
    assert decide(NoulAnswer(0.94)) == "manual_review"

def test_never_allows_an_uncertain_fraud_signal():
    for p in (x / 100 for x in range(3, 95)):
        assert decide(NoulAnswer(p)) != "allow"
```

`decide` takes an answer object rather than calling the model. Keep the model call at the edge and the
branching pure: you get fast tests and a function you can reason about.

## Next

- [The fast loop](/cookbook/the-70ms-loop/): keeping the call itself fast
- [Structured state](/cookbook/structured-state-ingestion/): what to put in `state`
