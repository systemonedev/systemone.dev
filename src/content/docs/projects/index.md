---
title: Projects
description: End-to-end builds you can ship, with the numbers to expect.
sidebar:
  order: 0
  label: Overview
---

Full systems, not snippets. Each project assumes you've read the
[fuzzy if-statement](/cookbook/fuzzy-if-statement/) and picks up from there. All code uses the
[`systemone-client`](https://pypi.org/project/systemone-client/) and runs against Kenning, Clef or Jev.

## [Security: phishing, agent firewall, alert triage](/projects/cybersecurity/)
Three security builds, starting with phishing triage, the one with published benchmark results.

**You'll build:** an email triage service that quarantines, delivers or escalates; a firewall
middleware in front of an expensive agent, with fail-closed degradation and a red-team suite; and a SOC
alert triage pipeline.

## [Data engineering: structuring messy data](/projects/data-engineering/)
Turning unstructured records into structured fields at pipeline scale, with probability-aware quality
gates.

**You'll build:** a batch pipeline with checkpointing, a review queue fed by the uncertain band, and
the cost controls that keep it viable at millions of rows.

## [Moderation and triage: scoring high-volume content](/projects/moderation-triage/)
A three-tier moderation system where the model handles the confident majority and people see only what
genuinely needs a person.

**You'll build:** a multi-policy moderation service, a priority-ordered review queue, an appeals path,
and the metrics that show it's working.

---

:::note[Bring your project]
Built something with a System One model? Projects are the most valuable thing you can contribute,
especially with real numbers. See [contributing](/community/contributing/).
:::
