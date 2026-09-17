---
title: Concepts
description: The mental model for decision-native AI — mostly a matter of unlearning what generative AI taught you.
sidebar:
  order: 0
  label: Overview
---

This is the unlearning section.

If you have spent the last few years building on generative models, you have absorbed a set of
habits — prompt engineering, output parsing, retry loops, treating a model's self-reported
confidence as decoration. Almost all of it is unnecessary here, and some of it is actively
harmful.

These four pages replace it.

## [System 1 vs System 2 AI](/concepts/system1-vs-system2/)
The core mental model, borrowed from Kahneman. Fast reflexes versus slow deliberation, and why
the AI landscape is splitting along that line. **Start here.**

## [RLCD vs RLHF](/concepts/rlcd-vs-rlhf/)
Why a model trained to be *helpful* and a model trained to be *calibrated* behave so
differently in production, and why you cannot prompt your way from one to the other.

## [The Zero Hallucination Guarantee](/concepts/zero-hallucination/)
What "zero hallucination" actually claims — and, more importantly, what it does not. Removing
token generation removes a category of failure. It does not remove being wrong.

## [Understanding Calibrated Confidence](/concepts/calibrated-confidence/)
How to read a probability score, how to verify that it means what it says, and how to pick
thresholds from your cost of error instead of from vibes.
