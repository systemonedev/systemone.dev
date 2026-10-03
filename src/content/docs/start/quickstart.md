---
title: 'Quickstart: your first decision'
description: Run an open System One model on your own machine and get a calibrated, typed decision back in about ten minutes.
sidebar:
  order: 2
---

The goal: send one messy email to a System One model running on your machine and get back typed
answers you can branch on. You won't write a prompt or a JSON parser.

You need Python 3.10 or later. A GPU helps but isn't required.

## 1. Get a model

Pick one:

**A. In your own Python process.** This is the fastest way to try it, and runs on CPU or GPU:

```bash
pip install "systemone[local]"
```

```python
from systemone import Kenning
model = Kenning.from_pretrained("systemonedev/kenning-large-v0.4")   # downloads ~0.9 GB once
```

**B. As a server, with the dashboard.** This is the way to run it for real. It needs Docker and an
NVIDIA GPU:

```bash
git clone https://github.com/systemonedev/systemone-builder && cd systemone-builder
cp .env.example .env              # set S1_REDIS_PASSWORD (openssl rand -hex 24)
echo "S1_KENNING_MODEL=systemonedev/kenning-large-v0.4" >> .env
docker compose up -d              # Kenning on 127.0.0.1:8093, dashboard on http://localhost:3090
pip install systemone
```

```python
from systemone import Client
model = Client("http://localhost:8093")
```

Both objects have the same `system_one()` method. Everything below works with either.

## 2. Ask your first questions

```python title="quickstart.py"
from systemone import Noul, Choice, Score

r = model.system_one(
    state={"email": {
        "from": "security@paypa1-support.com",
        "subject": "Your account will be closed",
        "body": "URGENT: we detected unusual activity. Verify your identity within 24 hours "
                "at http://paypa1-support.com/verify or your account will be closed.",
    }},
    questions={
        "phishing": Noul("Is this email a phishing attempt?"),
        "kind": Choice("What kind of email is this?", {
            "phishing": "Tries to steal credentials, money or access",
            "spam": "Unwanted marketing",
            "legitimate": "A genuine message from a real sender",
        }),
        "pressure": Score("How much pressure does the sender put on the reader?",
                          ["none", "some", "a lot"]),
    },
)
print(r.raw["answers"])
```

What `kenning-large-v0.4` returns, in one pass, on one RTX 3090:

```json
{
  "phishing": { "type": "noul", "noul": 0.9045 },
  "kind": {
    "type": "choice", "choice": "phishing", "confidence": 0.7177,
    "probabilities": { "phishing": 0.8118, "spam": 0.1495, "legitimate": 0.0387 }
  },
  "pressure": {
    "type": "score", "score": 1.8091, "confidence": 0.7484,
    "legend": { "0": "none", "1": "some", "2": "a lot" },
    "probabilities": { "0": 0.0231, "1": 0.1446, "2": 0.8322 }
  }
}
```

On CPU the same request takes about a second, and the last digits differ slightly (0.9036 instead of
0.9045): CPUs compute in float32, GPUs in bfloat16. On the same hardware, the same request always
gives the same answer.

Three things to notice:

1. **Every answer is one of the options you gave.** A choice can't come back as `"Phishing!"` or as
   a paragraph, so there's nothing to parse.
2. **You get a probability for every option**, not just the winner. The model put 15% on spam.
   That's information you'd never get from a generated label.
3. **`state` is your data as it is.** You passed a dict, not a prompt. The question carries the
   instructions; the state carries the facts.

## 3. Branch on it

This is the part that changes how you write code. You're writing an `if`, not a prompt:

```python title="triage.py"
def triage(email):
    r = model.system_one(state={"email": email},
                         questions={"phishing": Noul("Is this email a phishing attempt?")})
    p = r.nouls["phishing"].noul
    if p >= 0.9:
        return "quarantine"           # sure it is
    if p <= 0.1:
        return "deliver"              # sure it isn't
    return "ask_a_person"             # everything in between
```

The email above scores 0.90, right at the line: this policy would quarantine it, and anything a
little less certain goes to a person. That middle band is the point. The model decides the cases it
is sure about, and you decide what "sure" means. Pick the thresholds from the cost of each mistake,
then [check them on your own data](/concepts/calibrated-confidence/).

:::caution[A noul is a float]
Never write `if r.nouls["phishing"].noul:`. Since `bool(0.02)` is `True`, that line quarantines
everything. Always compare against a threshold.
:::

## 4. Measure before you automate

Before a model acts on its own, measure it on labelled examples of **your** data. SystemOne
Builder's **Verify** page, or `systemone bench`, reports accuracy, calibration, and how many items the
model would decide on its own at your thresholds, including how many dangerous ones it would wave
through. That last number is the one to watch.

## Where to go next

- **Understand what the numbers promise** → [Calibrated confidence](/concepts/calibrated-confidence/)
- **Learn the request and answer shapes** → [The wire format](/concepts/wire-format/)
- **Feed it real production state** → [Structured state](/cookbook/structured-state-ingestion/)
- **Build the whole thing** → [Phishing and alert triage](/projects/cybersecurity/)
