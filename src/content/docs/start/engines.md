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
used for training. Benchmarks below are `kenning-large-v0.5` (the current build); Clef is `clef-flash`
and Jev is `jev-latest`, run for comparison only and never trained on. The published Apache-2.0 download
is still `kenning-large-v0.4`; v0.5 is documented in the
[Kenning docs](https://github.com/systemonedev/systemone-builder/blob/main/docs/kenning.md).

### General decisions (the headline)

The `general` suite: 1,328 held-out items, 30 questions in 7 families of state. Accuracy per family, and
the mean across the families:

| Family | Kenning v0.5 | Clef | Jev |
|---|---|---|---|
| **Mean over families** | **0.653** | 0.791 | 0.830 |
| Text: evidence, sentiment, toxicity, prompt injection, intent, topic | 0.756 | 0.841 | 0.834 |
| Conversations: which service a dialogue is about | 0.979 | 1.000 | 1.000 |
| Answer quality: helpful, correct | **0.479** | 0.447 | 0.498 |
| Agent decisions: right tool call, function call, task completed | 0.727 | 0.793 | 0.900 |
| Records: refunds, spending limits, access rules over JSON | 0.587 | 0.857 | 0.921 |
| Tables: is a statement true | 0.520 | 0.860 | 0.940 |
| Logs: is a service failing, which one | 0.520 | 0.740 | 0.720 |
| Latency per request (p50) | 35 ms | 125 ms | 152 ms |

Kenning v0.5 already **beats both big engines on answer quality**, and is close on text and conversation,
at a twentieth of Clef's size and ~4x its speed. It is well behind on the decisions that need computation
over the state — records, tables, logs — because the 435M cross-encoder scores each option in one short
pass with nowhere to add numbers or scan a column. That is an architecture limit, and it is what the next
version changes.

### In development: Kenning-XL (v0.6)

Kenning-XL replaces the cross-encoder with a small **decoder** that reasons over the whole state, and adds
a **deliberate mode** that works through a short reasoning chain before it answers — trained on
ground-truth chains the builder's rule generators compute for free. Served as a two-tier cascade (the fast
reflex for what it already wins, the deliberate reasoner for records and tables):

| Family | v0.5 | **v0.6 (cascade)** | Clef | Jev |
|---|---|---|---|---|
| **Mean over families** | 0.653 | **0.720** | 0.791 | 0.830 |
| agent | 0.727 | **0.867** | 0.793 | 0.900 |
| tables | 0.520 | **0.740** | 0.860 | 0.940 |
| records | 0.587 | **0.654** | 0.857 | 0.921 |

v0.6 **halves the gap to Clef**, beats it on agent decisions and answer quality, and more than doubles the
hardest arithmetic task (daily-limit checks 0.42 → 0.81) through learned reasoning. It still trails Clef on
records, tables and logs. It is experimental — on the [`kenning-xl` branch](https://github.com/systemonedev/systemone-builder/tree/kenning-xl),
not yet a published model — and the honest open items are in the
[design notes](https://github.com/systemonedev/systemone-builder/blob/main/docs/kenning-xl-design.md).

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
