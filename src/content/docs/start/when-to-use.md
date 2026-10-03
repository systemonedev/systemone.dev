---
title: Is System One right for my problem?
description: An honest decision tree for choosing between decision-native models, generative models, and neither.
sidebar:
  order: 3
---

The fastest way to lose faith in a new architecture is to point it at the wrong problem. Here
is the honest version.

## Use System One when all of these are true

1. **The answer is a choice, not a composition.** You need one of *n* labels, a score, or a
   structured verdict — not prose, not code, not a summary.
2. **You know the categories in advance.** Or you can enumerate them at request time.
3. **Latency or volume actually matters.** You are in a request path, a pipeline, or a stream.
4. **Being wrong has a cost you want to manage explicitly.** You want to say "automate above
   95%, escalate below" and mean it.

Classic fits: agent guardrails, API and queue routing, SOC alert triage, content moderation,
lead scoring, document classification, data cleaning at pipeline scale, feature extraction.

## Use a generative model (System Two) when any of these are true

- The output is **generated content** — a reply, a summary, a migration, an email.
- The task needs **multi-step reasoning** where intermediate work matters.
- The **output space is open-ended** and cannot be enumerated.
- It is a **one-off or low-volume** task where a two-second wait costs nothing.

## Use both — this is the common answer

Most production systems that get this right use a System One model as the **router** and a
generative model as the **worker**:

```python title="router.py"
from systemone import Client, Choice

client = Client("http://localhost:8093")

def handle(user_id, message):
    # Tens of milliseconds: decide what kind of problem this is.
    r = client.system_one(state={"message": message}, questions={"intent": Choice(
        "What does the user want?", {
            "billing_lookup": "See invoices, charges or payment history",
            "password_reset": "Regain access to their account",
            "abuse": "Spam, threats or harassment",
            "open_question": "Anything else",
        })})
    intent = r.choices["intent"]
    if intent.probabilities[intent.choice] < 0.9:
        return escalate_to_human(message)

    match intent.choice:
        case "billing_lookup":
            return db.get_invoices(user_id)        # no model needed at all
        case "password_reset":
            return auth.send_reset_link(user_id)   # no model needed at all
        case "abuse":
            return block_and_log(user_id)
        case "open_question":
            return llm.chat(message)               # the expensive path, taken rarely
```

Two of those four branches need no model at all. That is usually where the cost savings
actually come from — not from making the LLM cheaper, but from not calling it.

## Use neither when

- **A regex or a lookup table works.** If the rule is `status === 'cancelled'`, write that.
  A decision model is for fuzzy input, not for logic you can already express.
- **You need an auditable legal or safety rule.** Calibrated is not the same as deterministic.
  A model at 0.99 is still wrong once in a hundred.
- **You have no labelled data and no way to evaluate.** You will not be able to tell whether
  it is working, and "it seems fine" is not a threshold.

## The honest failure modes

System One is not magic, and it is worth knowing where it hurts before you commit:

| Failure mode | What it looks like | What to do |
| :--- | :--- | :--- |
| **Bad category design** | Confidence sits at 0.4–0.6 constantly | Your categories overlap. Split or merge them. |
| **Distribution shift** | Accuracy quietly drops after a product launch | Monitor confidence distribution, not just accuracy. |
| **Threshold theatre** | Threshold set to 0.95 because it "sounds safe" | Derive it from a labelled sample and your cost of error. |
| **Missing category** | Real inputs that fit nothing you listed | Always include an `other` / `unclear` category. |

Every one of these is covered in the [Cookbook](/cookbook/).
