---
title: Cookbook
description: Integration patterns you can paste into a real codebase.
sidebar:
  order: 0
  label: Overview
---

Patterns, not theory. Every page here is Python you can lift, using the
[`systemone` client](https://pypi.org/project/systemone/), with the reasoning for why it's shaped that
way. It runs against Kenning, Clef or Jev unchanged.

## [The "fuzzy" if-statement](/cookbook/fuzzy-if-statement/)
The foundational pattern: routing logic built on probability bands. Thresholds in config, the
three-band pattern, the ordering mistake everyone makes, and testing.

## [The fast loop](/cookbook/the-70ms-loop/)
Keeping a decision call genuinely fast: one request for all questions, concurrency, caching, timeouts,
and the fallback you need when the model is slow or down.

## [Structured state](/cookbook/structured-state-ingestion/)
How to turn logs, records, events and multi-field objects into state a model evaluates well. The
highest-leverage and most-skipped step.

## [Agent guardrails](/cookbook/agent-guardrails/)
Putting a System One model in front of an agent: input screening, tool-call gating, output checks,
and the monitoring that catches drift before your users do.

---

:::tip[Contributing a pattern]
Have one that works in production? The Cookbook is the easiest place to contribute: see
[how to add a page](/community/contributing/).
:::
