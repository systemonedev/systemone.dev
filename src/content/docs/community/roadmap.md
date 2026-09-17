---
title: Roadmap
description: What is here, what is planned, and where help is most useful.
sidebar:
  order: 2
---

Public and revised as the site grows. Items marked **help wanted** are the ones where a
contributor would make the most difference.

## Shipped

- **Concepts** — System 1 vs System 2, RLCD vs RLHF, zero hallucination, calibrated confidence
- **Cookbook** — fuzzy if-statement, the 70ms loop, structured state ingestion, agent guardrails
- **Projects** — security firewall, data engineering pipeline, moderation & triage
- **Start Here** — orientation, quickstart, and an honest "should I use this" decision tree
- **Blog** with RSS

## Next

**A vendor-neutral model comparison page.** A maintained table of decision-native models —
latency, calibration methodology, category limits, pricing, availability. The single most
requested thing and the hardest to keep honest. **Help wanted.**

**Runnable examples repo.** Each Cookbook pattern as a working, tested repo rather than a
snippet. Starting with the firewall.

**A calibration toolkit.** Package up the
[calibration check](/concepts/calibrated-confidence/#verifying-calibration-yourself) as a small
library: reliability diagrams, Brier and ECE scores, drift alerts. **Help wanted.**

**Python throughout.** Every example is currently JavaScript. A large part of this audience is
in data engineering and ML, where that is the wrong default. **Help wanted.**

## Later

- **Cost modelling** — a calculator for System 1 routing vs pure System 2, with honest assumptions
- **Evaluation guide** — building a labelled set, sampling, measuring without fooling yourself
- **Domain sections** — fintech, healthcare triage, logistics, ad review
- **Case studies** — real deployments, named or anonymous, with real numbers
- **Hybrid architectures** — deeper treatment of System 1 routing to System 2 workers
- **Glossary** — RLCD, calibration, proper scoring rules, decision-native, and the rest

## Explicitly not doing

**Becoming a product site for any vendor.** Including Jev. The moment this reads as marketing it
stops being useful.

**A benchmark leaderboard.** Ranking models on a single number invites gaming and misleads
readers whose workload looks nothing like the benchmark. Methodology-first comparisons only.

**Hosted tooling or an API.** This is a documentation and community site. It stays static,
fast, and cheap to run.

## Influencing this

Open an issue or start a discussion on
[GitHub](https://github.com/systemone-dev/systemone.dev). Pages people actually want get
prioritised over pages we assumed they wanted — say what you came here looking for and did not
find.
