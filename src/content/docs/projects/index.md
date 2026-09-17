---
title: Projects
description: End-to-end builds you can ship this week.
sidebar:
  order: 0
  label: Overview
---

Full systems, not snippets. Each project assumes you have read the
[fuzzy if-statement](/cookbook/fuzzy-if-statement/) and picks up from there.

## [Security: The Zero-Latency AI Firewall](/projects/cybersecurity/)
Three architectures for high-volume security work — an agent firewall, SOC alert and phishing
triage, and a semantic code linter. The flagship build.

**You will build:** a reverse-proxy middleware that screens prompts before they reach an
expensive reasoning model, with fail-closed degradation and a red-team suite in CI.

## [Data Engineering: Map-reducing messy data](/projects/data-engineering/)
Turning unstructured records into structured features at pipeline scale, with confidence-aware
quality gates.

**You will build:** a batch classification pipeline with checkpointing, a human-review queue fed
by the uncertain band, and cost controls that keep it viable at millions of rows.

## [Moderation & Triage: Scoring high-volume content](/projects/moderation-triage/)
A three-tier moderation system where the model handles the confident majority and humans see
only what genuinely needs a person.

**You will build:** a multi-policy moderation service, a priority-ordered review queue, an
appeals path, and the metrics that tell you it is working.

---

:::note[On the code in these projects]
Examples use Jev because it is the most complete System 1 implementation shipping today. The
architecture applies to any decision-native model — swap the client, keep the shape. We would
genuinely like more frameworks represented here;
[contributions welcome](/community/contributing/).
:::
