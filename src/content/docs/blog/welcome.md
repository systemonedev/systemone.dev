---
title: 'Why We Built SystemOne.dev, and an Open System One Model'
description: Decision models are a real architectural shift with almost no shared, open engineering around them. We're starting both.
date: 2026-10-03T13:00:00Z
authors:
  - maintainers
excerpt: Every team building on decision models is rediscovering the same patterns in private, on closed models. SystemOne.dev writes the patterns down, and Kenning and SystemOne Builder make the models open.
tags: [meta, community, kenning]
---

Something has been quietly true for a while now: a large share of what teams use large language models
for isn't generation. It's classification, routing, scoring and gating: decisions dressed up as text.

We noticed it the way most people do, by writing the same defensive code for the fifth time:

```python
res = llm.chat(messages=[...])                    # "ONLY RETURN VALID JSON..."
try:
    parsed = json.loads(strip_fences(res.text))
except json.JSONDecodeError:
    parsed = retry_with_stricter_prompt(text)
if parsed.get("category") not in ALLOWED:
    parsed = {"category": "unknown", "confidence": 0}
```

None of that is business logic. All of it exists because we asked a text generator a multiple-choice
question and got back a paragraph.

## The gap

**System One models** fix that problem directly: they answer typed questions about your program's
state with a probability for every option, in tens of milliseconds, without generating text. The
architecture is real and it works.

Two things were missing.

**The engineering literature.** Search for how to pick a threshold and you find "0.95 is a good starting
point". Search for what calibration drift looks like in production and you find research papers. Every
team is working it out alone, and making the same [four mistakes](/blog/four-mistakes/).

**Open models.** The best-known System One model was a hosted service. You couldn't run it on your own
data, inspect how it was trained, or change it.

## What we're launching

- **[SystemOne.dev](/)**: the patterns, written down once, with code that runs.
- **[Kenning](https://huggingface.co/systemonedev/kenning-large-v0.5)**: an open System One model under
  Apache-2.0. It's 435M parameters, runs on a ~2 GB GPU footprint or a CPU, and its training data and
  licences are documented.
- **[SystemOne Builder](https://github.com/systemonedev/systemone-builder)**: an open toolkit to serve,
  train, distil and benchmark your own System One models on one GPU, from a dashboard.
- **[`systemone-client`](https://pypi.org/project/systemone-client/)**: one Python client for Kenning, Cloudflare's Clef
  and TypeSafe's Jev. Switch engines by changing a URL.

## Two commitments

**We'll stay honest about limits.** Kenning v0.4 is faster and much smaller than the big engines, and
behind them on subtle phishing. We publish [those numbers](/start/engines/), not just the flattering
ones. "No hallucination" gets a page that spends as much space on
[what doesn't disappear](/concepts/zero-hallucination/#what-does-not-disappear) as on what does.
Calibration is something you verify on your own data, so every page tells you how.

**We'll stay open and engine-neutral.** The code, the weights, the benchmark suites and this site are
all open. Every engine that speaks the format is welcome here, and pages about other engines are welcome
contributions.

There's a version of this site that's more exciting to read and less useful to build on. We're not going
to write that one.

## Start here

- Want code running → [Quickstart](/start/quickstart/)
- New to the idea → [System One vs. System Two](/concepts/system1-vs-system2/)
- Not sure it fits → [Is System One right for my problem?](/start/when-to-use/)
- Want to help → [Contributing](/community/contributing/)

If you're already running a decision model in production, we especially want to hear from you. Real
numbers on real workloads are the scarcest thing in this whole space.
