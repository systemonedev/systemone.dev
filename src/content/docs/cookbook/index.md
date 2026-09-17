---
title: Cookbook
description: Integration patterns you can paste into a real codebase.
sidebar:
  order: 0
  label: Overview
---

Patterns, not theory. Every page here is code you can lift, with the reasoning for why it is
shaped that way.

## [The "Fuzzy" If-Statement](/cookbook/fuzzy-if-statement/)
The foundational pattern: routing logic built on confidence bands. Covers threshold
configuration, the three-band pattern, the ordering mistake everyone makes, and testing.

## [Handling the 70ms Loop](/cookbook/the-70ms-loop/)
Architecture for keeping a decision call genuinely fast — batching, parallel evaluation,
caching, timeouts, and the fallback behaviour you need when the model is slow or down.

## [Structured State Ingestion](/cookbook/structured-state-ingestion/)
How to turn logs, records, events, and multi-field objects into the input a decision model
evaluates well. The highest-leverage and most-skipped step.

## [Agent Guardrails & Verification](/cookbook/agent-guardrails/)
Putting a decision model in front of an agent: input screening, output verification, tool-call
gating, and the monitoring that catches drift before your users do.

---

:::tip[Contributing a pattern]
Have one that works in production? The Cookbook is the easiest place to contribute — see
[how to add a page](/community/contributing/).
:::
