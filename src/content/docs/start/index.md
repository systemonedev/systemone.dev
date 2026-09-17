---
title: Welcome to SystemOne.dev
description: A five-minute orientation to decision-native AI and what this site is for.
sidebar:
  order: 1
---

Most AI content assumes you want a model that talks. This site assumes you want a model that
**decides** — and then gets out of your way.

## What this site is

SystemOne.dev is a community-run developer hub for **System 1 AI**: models that give up token
generation entirely in order to return typed, probabilistic decisions in tens of milliseconds.

It is organised into four sections, and they are meant to be read in roughly this order:

| Section | What it gives you |
| :--- | :--- |
| [Concepts](/concepts/) | The mental model. Mostly unlearning what generative AI taught you. |
| [Cookbook](/cookbook/) | Patterns you paste into a real codebase. |
| [Projects](/projects/) | End-to-end builds you can ship. |
| [Blog](/blog/) | Field notes, benchmarks, and community write-ups. |

## What this site is not

- **Not a product site.** We are vendor-neutral. Jev is used in examples because it is the
  most complete System 1 implementation shipping today, but the patterns here apply to any
  decision-native model.
- **Not anti-LLM.** System 2 models are extraordinary at what they are for. The argument on
  this site is about *routing*, not replacement — most production AI systems need both.

## The one idea

A generative model answers `"what should I say?"`. A decision model answers
`"which of these, and how sure am I?"`.

That second question has a typed answer. Typed answers can be branched on. Code that branches
on typed answers is code you can test, monitor, and trust.

```javascript
// This is the whole pitch.
const { category, confidence } = await jev.evaluate({
  input: rawState,
  categories: ['approve', 'review', 'reject'],
});

if (confidence > 0.95) applyAutomatically(category);
else escalateToHuman(rawState);
```

## Next

- New to the distinction? → [System 1 vs System 2 AI](/concepts/system1-vs-system2/)
- Want code running now? → [Quickstart](/start/quickstart/)
- Not sure it fits your problem? → [Is System 1 right for my problem?](/start/when-to-use/)
