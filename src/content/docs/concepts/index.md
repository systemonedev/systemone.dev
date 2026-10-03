---
title: Concepts
description: The mental model for System One decision models, mostly a matter of unlearning what generative AI taught you.
sidebar:
  order: 0
  label: Overview
---

This is the unlearning section.

If you've spent the last few years building on generative models, you've absorbed a set of habits:
prompt engineering, output parsing, retry loops, treating a model's self-reported confidence as
decoration. Almost all of it is unnecessary here, and some of it is actively harmful.

These pages replace it.

## [System One vs. System Two AI](/concepts/system1-vs-system2/)
The core mental model, borrowed from Kahneman: fast reflexes versus slow deliberation, and why AI
systems are splitting along that line. **Start here.**

## [The wire format](/concepts/wire-format/)
Exactly what goes in (state and typed questions) and what comes out (typed answers with
probabilities), field by field. The same format works for Kenning, Clef and Jev.

## [What "no hallucination" means (and doesn't)](/concepts/zero-hallucination/)
Removing token generation removes a whole class of failure: malformed and invented output. It
doesn't remove being wrong, and it doesn't make adversarial input harmless.

## [Understanding calibrated confidence](/concepts/calibrated-confidence/)
How to read the probabilities, how to verify they mean what they say, and how to pick thresholds from
your cost of error instead of from vibes.

## [How System One models are trained](/concepts/how-models-are-trained/)
Cross-encoders, calibration by temperature, and distillation from a larger teacher: why these models
behave so differently from chat models, and what that means for you.
