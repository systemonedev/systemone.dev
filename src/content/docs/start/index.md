---
title: Welcome to SystemOne.dev
description: A five-minute orientation to System One decision models and what this site is for.
sidebar:
  order: 1
---

Most AI content assumes you want a model that talks. This site assumes you want a model that
**decides**, and then gets out of your way.

## What a System One model is

A model that answers typed questions about your program's state, without generating text:

| You ask | You get back |
| :--- | :--- |
| a **noul** (yes/no): "Is this email phishing?" | `noul`: the probability of yes |
| a **choice**: "Which team should handle this ticket?" + options | the chosen option and a probability for every option |
| a **score**: "How urgent is it?" + ordered levels | a probability for every level, and their weighted average |

Every question in a request is answered in one pass. The answer is always one of the options you
gave, so there's nothing to parse and nothing to retry. The name comes from the psychology of fast,
intuitive judgement (System 1) versus slow, deliberate reasoning (System 2). Most good AI systems
need both, and this site is about the first.

## The one idea

A generative model answers *"what should I say?"*. A decision model answers *"which of these, and
how sure am I?"*. That second answer is typed, so you can branch on it, test it and monitor it:

```python
from systemone import Client, Choice

client = Client("http://localhost:8093")
r = client.system_one(
    state=application,                       # your real JSON, not a prompt
    questions={"decision": Choice("Should this application be approved?",
                                  {"approve": None, "review": None, "reject": None})},
)
d = r.choices["decision"]
if d.choice != "review" and d.probabilities[d.choice] >= 0.95:
    apply_automatically(d.choice)
else:
    send_to_reviewer(application, d.probabilities)
```

## What's here

| Section | What it gives you |
| :--- | :--- |
| [Concepts](/concepts/) | The mental model, mostly unlearning what generative AI taught you |
| [Cookbook](/cookbook/) | Patterns to paste into a real codebase |
| [Projects](/projects/) | End-to-end builds, with benchmarks |
| [Blog](/blog/) | Field notes, results and community write-ups |

## What this site is not

- **Not a product brochure.** It's run by the maintainers of the open-source
  [SystemOne Builder](https://github.com/systemonedev/systemone-builder) and the
  [Kenning](https://huggingface.co/systemonedev/kenning-large-v0.5) models. The patterns apply to every
  engine that speaks the format, including hosted ones: see [Engines](/start/engines/). We publish our
  benchmarks, including where Kenning loses.
- **Not anti-LLM.** Generative models are extraordinary at what they're for. The argument here is
  about *routing*: send the decisions to a fast model, and the writing and reasoning to a slow one.

## Next

- Want code running now? → [Quickstart](/start/quickstart/)
- Not sure it fits your problem? → [Is System One right for my problem?](/start/when-to-use/)
- New to the distinction? → [System One vs System Two](/concepts/system1-vs-system2/)
