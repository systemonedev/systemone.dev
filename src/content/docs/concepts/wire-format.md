---
title: The Wire Format
description: Exactly what a System One request and answer contain, field by field. The same format works with Kenning, Clef and Jev.
sidebar:
  order: 2
---

Every System One engine on this site speaks one HTTP format: `POST /v1/systemone`. Learn it once and
your code moves between engines by changing a URL. The [`systemone-client`](https://pypi.org/project/systemone-client/)
builds and parses it for you, but it's worth knowing what's on the wire.

## The request

```json
{
  "state": {
    "ticket": { "subject": "Refund?", "body": "I was charged twice this month." },
    "customer": { "plan": "pro", "tenure_months": 14 }
  },
  "questions": {
    "refund": { "type": "noul", "instructions": "Is the customer asking for a refund?" },
    "queue": {
      "type": "choice",
      "instructions": "Which queue should handle it?",
      "criteria": { "billing": "Charges, refunds, invoices", "account": null }
    },
    "tone": {
      "type": "score",
      "instructions": "How heated is the message?",
      "criteria": ["Polite", "Impatient", "Hostile"]
    }
  },
  "model": "kenning-large-v0.4"
}
```

| Field | Required | What it is |
| :--- | :--- | :--- |
| `state` | yes | The situation: a string, or a JSON object. Pass your real data, not a prompt. |
| `questions` | yes, at least one | Your question ids mapped to questions. Ids are yours, and they're the keys of the answers. |
| `model` | no | Which model to use, for servers that host several. |

### Questions

| `type` | `criteria` | Limits |
| :--- | :--- | :--- |
| `noul` (yes/no) | optional: a string or object clarifying what counts as yes | |
| `choice` (pick one) | **required**: `{option: description or null}` | 2–255 options |
| `score` (ordered scale) | **required**: the levels, lowest first | 2–10 levels |

`instructions` is the question itself, in plain language. One decision per question: "Is this
phishing?" and "Is this urgent?" are two questions, not one.

## The answer

```json
{
  "model": "kenning-large-v0.4",
  "answers": {
    "refund": { "type": "noul", "noul": 0.96 },
    "queue": {
      "type": "choice", "choice": "billing", "confidence": 0.9,
      "probabilities": { "billing": 0.95, "account": 0.05 }
    },
    "tone": {
      "type": "score", "score": 1.2, "confidence": 0.31,
      "legend": { "0": "Polite", "1": "Impatient", "2": "Hostile" },
      "probabilities": { "0": 0.1, "1": 0.6, "2": 0.3 }
    }
  },
  "usage": { "input_tokens": 211, "output_tokens": 0 }
}
```

| Field | Meaning |
| :--- | :--- |
| `noul` | Probability that the answer is yes. |
| `choice` | The option with the highest probability. |
| `probabilities` | Every option's (or level's) probability, summing to 1. Score levels are keyed by index. |
| `score` | The probability-weighted average level index, from 0 to n−1. |
| `legend` | Score level index → the level you gave. |
| `confidence` | How concentrated `probabilities` is: `(max p − 1/n) / (1 − 1/n)`, 0 for an even split, 1 for certain. Not the winner's probability: [why that matters](/concepts/calibrated-confidence/#reading-an-answer). |
| `usage.output_tokens` | Always 0. Nothing is generated. |

Some servers add fields. Kenning and SystemOne Builder add `latency_ms`. Clients should ignore fields
they don't know.

## With curl

```bash
curl -s http://localhost:8093/v1/systemone -H 'content-type: application/json' -d '{
  "state": "Your invoice is attached, click here to pay now",
  "questions": {"phishing": {"type": "noul", "instructions": "Is this a phishing attempt?"}}}'
```

Hosted engines take a key as `Authorization: Bearer <key>`.

## Design notes

- **All questions in a request are answered together**, in one pass over the state. Ask everything you
  need at once instead of one request per question.
- **Every answer comes back, typed.** An answer can't be missing, malformed or off-list: if the server
  can't answer, the whole request fails with an HTTP error instead of returning a partial answer.
- **State size is bounded.** Models read a limited number of tokens per question: Kenning reads 512 per
  (state, option) pair and truncates the state beyond that. Send the fields that matter. See
  [structured state](/cookbook/structured-state-ingestion/).

The format originated with TypeSafe AI's System One API. SystemOne.dev is not affiliated with TypeSafe
AI.
