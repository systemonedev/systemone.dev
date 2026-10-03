---
title: Roadmap
description: What's here, what's planned, and where help is most useful.
sidebar:
  order: 2
---

Public, and revised as the project grows. Items marked **help wanted** are where a contributor would
make the most difference. Discuss any of them in
[Discussions](https://github.com/systemonedev/systemone-builder/discussions).

## Shipped

- **Kenning v0.4**: an open System One model (Apache-2.0) with published benchmarks
- **SystemOne Builder**: serve, train, distil from Clef, benchmark and publish models, on one GPU
- **The `systemone` Python client**: one client for Kenning, Clef and Jev
- **This site**: concepts, cookbook, projects, all in Python and runnable

## Next

**Kenning that holds its own on subtle phishing.** Today it's at 0.75 on our held-out modern-email set,
against 0.90 for the big engines. Next: more realistic calm-lure and legitimate-twin training pairs, and a
permissively licensed real phishing corpus. **Help wanted:** labelled emails you can share under an open
licence.

**More benchmark suites.** Every suite is a small, hand-labelled, openly licensed set that's never
trained on: support tickets, moderation, intent routing, log triage. **Help wanted:** this is the easiest
way to make a real difference.

**A calibration toolkit.** The [calibration check](/concepts/calibrated-confidence/#verifying-calibration-yourself)
as a small library: reliability diagrams, Brier and ECE, drift alerts. **Help wanted.**

**A TypeScript client.** The wire format is simple; the client should exist for Node and the browser
too. **Help wanted.**

**Smaller and faster Kenning.** A base-size model for CPU-only and edge deployments.

## Later

- **Evaluation guide**: building a labelled set, sampling, and measuring without fooling yourself
- **Cost modelling**: System One routing versus an LLM for everything, with honest assumptions
- **Domain sections**: fintech, healthcare intake, logistics, ad review
- **Case studies**: real deployments, named or anonymous, with real numbers
- **Code review checks**: whether System One models can usefully read code diffs is an open question;
  we'd like a benchmark before we publish a pattern
- **Glossary**: calibration, proper scoring rules, distillation, and the rest

## Explicitly not doing

**Becoming a sales site.** Not for Kenning, not for anyone. The moment this reads as marketing it stops
being useful.

**A single-number leaderboard.** Ranking models on one number invites gaming and misleads readers whose
workload looks nothing like the benchmark. We publish per-suite results with methodology instead.

**Training on data we can't share the licence of.** Kenning's training data is permissively licensed or
generated, and listed in every model card. No outputs of services whose terms forbid it.

## Influencing this

Start a [discussion](https://github.com/systemonedev/systemone-builder/discussions) or open an issue. Things
people actually ask for get priority over things we assumed they wanted, so tell us what you came looking
for and didn't find.
