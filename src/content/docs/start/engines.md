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
used for training. Benchmarks below are `kenning-large-v0.6`, the current published model, with v0.5 shown
for comparison. Clef is `clef-flash` and Jev is `jev-latest`, run for comparison only and never trained on.
Both `kenning-large-v0.6` and `kenning-large-v0.5` are published Apache-2.0 downloads (Hugging Face); recipes
and full results are in the [Kenning docs](https://github.com/systemonedev/systemone-builder/blob/main/docs/kenning.md).

### General decisions (the headline)

The `general` suite: 1,328 held-out items, 30 questions in 7 families of state. Accuracy per family, and
the mean across the families:

| Family | **Kenning v0.6** | v0.5 | Clef | Jev |
|---|---|---|---|---|
| **Mean over families** | **0.753** | 0.653 | 0.791 | 0.830 |
| Text: evidence, sentiment, toxicity, prompt injection, intent, topic | 0.813 | 0.756 | 0.841 | 0.834 |
| Conversations: which service a dialogue is about | 1.000 | 0.979 | 1.000 | 1.000 |
| Answer quality: helpful, correct | **0.457** | 0.479 | 0.447 | 0.498 |
| Agent decisions: right tool call, function call, task completed | **0.827** | 0.727 | 0.793 | 0.900 |
| Records: refunds, spending limits, access rules over JSON | 0.651 | 0.587 | 0.857 | 0.921 |
| Tables: is a statement true | 0.680 | 0.520 | 0.860 | 0.940 |
| Logs: is a service failing, which one | **0.790** | 0.520 | 0.740 | 0.720 |
| Latency per request (p50) | 285 ms | 35 ms | 125 ms | 152 ms |

**Kenning v0.6** is a long-context (2,048-token) ModernBERT cross-encoder — a 400M reflex that sees the whole
state in one pass. It **beats Clef on agent decisions, conversation, answer quality and logs** (logs 0.79,
ahead of both Clef and Jev), and lifts the macro to **0.753 (from v0.5's 0.653)**, closing most of the gap to
Clef (0.791) while staying a twentieth of its size. The longer window costs latency — ~285 ms vs v0.5's 35 ms
— so **v0.5 stays the fast option** and v0.6 the accurate one. Records and tables still trail the big engines:
those need computation, not just more context, which is what the experimental decoder below explores.

### Experimental: Kenning-XL (decoder)

Kenning-XL is a research line that replaces the cross-encoder with a small **decoder** reasoning over the
whole state, with a **deliberate mode** — a short gold-trace reasoning chain before it answers, trained on
chains the builder's rule generators compute for free. It is strong on the computation-heavy families
through learned reasoning (a 4B decoder reaches records ≈ 0.79, tables ≈ 0.78) and more than doubles the
hardest arithmetic task (daily-limit checks 0.42 → 0.81).

But the long-context ModernBERT reflex (**v0.6**, above) turned out to be the better overall path: simpler,
one pass, higher macro (**0.753** vs the decoder's ~0.69 as served), ahead on logs, and far faster to serve.
So **v0.6 is what's published**, and the decoder continues as research aimed at records and tables. Its
engine, trainer and docs are **merged into
[`main`](https://github.com/systemonedev/systemone-builder)**; it is experimental and not a published model.
The method and the honest open items are in
[docs/kenning.md](https://github.com/systemonedev/systemone-builder/blob/main/docs/kenning.md) and the
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
model = Kenning.from_pretrained("systemonedev/kenning-large-v0.5")

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
