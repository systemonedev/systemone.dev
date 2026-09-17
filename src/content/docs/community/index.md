---
title: Community
description: What SystemOne.dev is for, who runs it, and how to get involved.
sidebar:
  order: 0
  label: Overview
---

SystemOne.dev is a community-run hub for developers building on decision-native AI. It is not a
product site and it is not owned by a model vendor.

## What we are trying to build

There is a real architectural shift happening — models that return typed decisions instead of
generated text — and almost no shared engineering literature about it. Every team working on
this is currently rediscovering the same patterns, making the same threshold mistakes, and
learning the same lessons about drift on their own.

This site is where that knowledge gets written down once.

## Our stance

**Vendor-neutral.** Jev appears throughout the examples because it is the most complete System 1
implementation shipping today. That is a practical choice, not an endorsement, and we actively
want more frameworks represented. If you work on one, [open a PR](/community/contributing/).

**Honest about limits.** Every page on this site that makes a strong claim also says where it
breaks down. "Zero hallucination" is
[carefully bounded](/concepts/zero-hallucination/#what-does-not-disappear). Calibration is
presented as something you [verify](/concepts/calibrated-confidence/), not something you trust.
We would rather be useful than impressive.

**Not anti-LLM.** Generative models are extraordinary at generation. The argument here is about
routing work to the right architecture — and most real systems need both.

**Practical over theoretical.** If a page cannot show you code you could actually run, it
probably does not belong here.

## Get involved

- **[Contributing](/community/contributing/)** — how to add or fix a page, and what we are
  actively looking for
- **[Roadmap](/community/roadmap/)** — what is planned, and where help is most useful
- **[GitHub](https://github.com/systemone-dev/systemone.dev)** — issues, discussions, PRs
- **[Blog](/blog/)** — field notes, benchmarks, and write-ups from the community

## Good first contributions

The highest-value things you can write, roughly in order:

1. **A benchmark from your own workload.** Real latency and accuracy numbers on real data are
   the scarcest resource in this whole space.
2. **A pattern that failed.** Negative results are underrated and nobody publishes them. A page
   about a threshold strategy that did not survive contact with production would get read.
3. **A framework other than Jev.** Anything that widens the site beyond one implementation
   directly serves the core goal.
4. **A domain we do not cover.** Fintech, healthcare triage, logistics, ad review. The patterns
   generalise; the specifics do not, and the specifics are what people need.
