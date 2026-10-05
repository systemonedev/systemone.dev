---
title: 'Engines: Kenning, Clef, Jev'
description: The System One engines you can use today, how they compare on the same benchmarks, and how to point your code at each.
sidebar:
  order: 4
---

Several engines speak the same System One wire format (`POST /v1/systemone`). The `systemone`
client works with all of them, so the code on this site runs unchanged on each. You switch engines
by changing a URL.

| | **Kenning** | **Clef** | **Jev** |
|---|---|---|---|
| Made by | the SystemOne Builder community | Cloudflare | TypeSafe AI |
| Licence | Apache-2.0 weights | Apache-2.0 weights | hosted service, paid |
| Runs | on your machine | on your machine | on TypeSafe's API |
| Size / hardware | 435M parameters, ~2 GB of GPU memory, or CPU | 9B parameters, a 24 GB GPU | n/a |
| Determinism | same request, same answer (same hardware) | yes, locally | per TypeSafe |
| You can train it further | yes: SystemOne Builder | as a base, yourself | no |

## Same benchmarks, side by side

We run every engine through the same suites with `systemone bench` (in
[SystemOne Builder](https://github.com/systemonedev/systemone-builder)). None of these suites were
used for training. Kenning is `kenning-large-v0.4`; Clef is `clef-flash`; both on one RTX 3090.

### General decisions (the headline)

The `general` suite: 1,328 held-out items, 30 questions in 7 families of state. Macro accuracy (the
mean over questions, so each counts equally):

| Family | Kenning | Clef |
|---|---|---|
| **All 30 questions** | **0.625** | **0.813** |
| Text: evidence, sentiment, toxicity, prompt injection, intent, topic (14) | 0.754 | 0.841 |
| Conversations: which service a dialogue is about (1) | 0.958 | 1.000 |
| Answer quality: helpful, correct (2) | 0.377 | 0.447 |
| Agent decisions: right tool call, should call a function, task completed (3) | 0.553 | 0.793 |
| Records: refunds, spending limits, access rules, priorities over JSON (7) | 0.535 | 0.857 |
| Tables: is a statement true (1) | 0.480 | 0.860 |
| Logs: is a service failing, which one (2) | 0.290 | 0.740 |
| Latency per request (p50) | 34 ms | 149 ms |

Jev hasn't been run on this suite. We compare against it once Kenning matches Clef.

### Email suites

| Suite | Kenning | Clef | Jev |
|---|---|---|---|
| Modern emails (20 held out, incl. calm credential lures) | 0.75 | 0.90 | 0.90 |
| …phishing emails it was *sure* were safe (auto-closed) | **0** | 0 | 0 |
| Phishing dataset (50) | 0.78 | 0.96 | 0.96 |
| Out of domain: spam / emotion / news topic | 0.917 / 0.583 / 0.867 | 0.900 / 0.600 / 0.950 | 0.967 / 0.583 / 0.933 |
| Latency per request (p50) | 33–88 ms | 220–290 ms | ~150 ms incl. network |

How to read this honestly:

- **Kenning is close to Clef on text, and well behind on structured state.** On records, tables, agent
  steps and logs it is often near chance. It reads 512 tokens per option, so long logs get cut off, and
  its training data was mostly short text. Clef is a 9B language model with a decision head. If your
  state is a record or an agent step, measure Kenning on your own data before trusting it, or
  [train it for your problem](/concepts/how-models-are-trained/#training-for-your-own-problem).
- **It's about 20 times smaller and 4 times faster.** In the email suites it was right whenever it was
  sure, apart from one spam message: it stays humble rather than confidently wrong.
- **Small suites are noisy.** In a 50-item task, each item moves the number by 2 points. The suites are
  open: run them yourself, and add your own.
- Full method, per-task results and caveats are in the
  [Kenning docs](https://github.com/systemonedev/systemone-builder/blob/main/docs/kenning.md).

## Pointing the client at each engine

```python
import os
from systemone import Client, Kenning

# Kenning in-process (pip install "systemone-client[local]")
model = Kenning.from_pretrained("systemonedev/kenning-large-v0.4")

# Kenning or Clef served by SystemOne Builder (localhost only, no key)
kenning = Client("http://localhost:8093")
clef = Client("http://localhost:8094")            # docker compose --profile clef up -d clef

# TypeSafe Jev (your key; each request is billed under your TypeSafe agreement)
jev = Client("https://api.typesafe.ai", api_key=os.environ["TYPESAFE_API_KEY"], model="jev-latest")
```

All four objects take the same `system_one(state=..., questions=...)` call and return the same
`Response`.

## Which one should I use?

- **Prototyping, privacy-sensitive data, high volume, or no budget:** Kenning. It's free, runs
  anywhere, and you can fine-tune it on your own labelled data with SystemOne Builder.
- **Hardest judgement calls on your own hardware:** Clef, if you have a 24 GB GPU to give it.
  It's also a good teacher to [distil](/concepts/how-models-are-trained/) into a smaller model.
- **No GPU and no operations work:** Jev, as a hosted service.

You don't have to choose once. A common setup is Kenning first, escalating the uncertain middle band
to a bigger engine or to a person. See [the fuzzy if-statement](/cookbook/fuzzy-if-statement/).

:::note[Terms differ]
Kenning and Clef are open weights, so you can use their outputs for anything, including training.
TypeSafe's terms forbid using Jev's outputs to develop competing models, so never train on them.
SystemOne.dev is not affiliated with TypeSafe AI or Cloudflare.
:::
