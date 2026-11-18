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

- **Kenning v0.4, v0.5 & v0.6**: open System One models (Apache-2.0) up to 2,048 tokens (general macro **0.761**, beating Clef on agent decisions, conversations, answer quality and logs)
- **Kenning Phishing (`kenning-phishing-v1.1` & `kenning-phishing-long-v1.1`)**: domain-specialised Apache-2.0 phishing triage models with Stage-0 email/webpage pre-parsers, 50% signal dropout, `Clef-flash` soft-label distillation (`alpha=0.30`), hard-label empirical calibration, and a two-stage state-aware cascade (**0.868** 6-task macro and **0.917** `is_phish` accuracy on 48 hand-written counterfactuals; **0.953** accuracy / **0.984** ROC-AUC on 400 real `PhishNChips` emails; **0.963** accuracy / **0.992** ROC-AUC on 80 real `phreshphish` webpages)
- **SystemOne Builder**: serve, train, distil from Clef, benchmark against local and frontier LLMs (`openai:*`, `anthropic:*`, `gemini:*`, `openrouter:*`, `ollama:*`) and publish models, on one GPU
- **The general & third-party benchmarks**: 30 decision questions over text, tables, conversations, agent steps,
  records and logs, plus TypeSafe's `WorkflowEvals` (240 items), `phishing_counterfactual` (48 hand-written twins), and `phreshphish` (80 real test-split webpages)
- **Training for your own problem**: problem specs with teacher-written, blind-checked cases (`computer_use`, `insurance_claim`, `chat_moderation`, `phishing_triage`); importing
  your own labelled data; held-out suites; calibration on your data
- **The `systemone` Python client**: one client for Kenning, Clef and Jev
- **This site**: concepts, cookbook, projects, all in Python and runnable

## Next

**Decisions over computation-heavy records and tables.** On the general benchmark Kenning v0.6 is at **0.761**
against Clef's 0.791—ahead on agent steps and logs, and still behind on records (`0.681`) and tables (`0.680`)
that require multi-row arithmetic. Next: log/table counting traces and a single-engine cascade combining the
fast cross-encoder reflex with `Kenning-XL` deliberate reasoning.

**More problem specs and real test sets.** Specs for common decisions (agent guardrails, ticket routing,
claims, moderation, compliance checks) and, above all, small hand-labelled test sets from real data,
shared under an open licence. **Help wanted:** this is the easiest way to make a real difference.

**Broader real-world phishing corpora.** `kenning-phishing-v1.1` and `kenning-phishing-long-v1.1` reach **0.917**
accuracy (**0.972** ROC-AUC, **0.833** pair-flip) on the 48 hand-written counterfactuals, **0.950** (`1.000` ROC-AUC) on `modern2`, **0.953** (`0.984` ROC-AUC) on 400 real `PhishNChips` emails, and
**0.963** (`0.992` ROC-AUC) on 80 real `phreshphish` webpages. **Help wanted:**
additional anonymised corporate phishing and BEC test sets you can share under an open licence.

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
