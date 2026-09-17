---
title: 'RLCD vs. RLHF: Training for Calibration, Not Charisma'
description: Why a model trained to be helpful and a model trained to be calibrated behave so differently in production.
sidebar:
  label: RLCD vs. RLHF
  order: 2
---

Two models can see identical input and disagree about what the goal even is. That disagreement
starts in the training objective, and no amount of prompting moves it.

## RLHF optimises for a human saying "yes, that one"

**Reinforcement Learning from Human Feedback** works roughly like this: show humans two model
outputs, ask which they prefer, train a reward model on those preferences, then tune the model
to maximise that reward.

It works remarkably well for what it is for. It is also why generative models have the
personality they have — and why they behave the way they do when they are unsure.

Humans rate confident, fluent, complete answers higher than hedging ones. So the objective
rewards **sounding right**. A model that says "It's a phishing email — the domain is spoofed and
the urgency is a classic pressure tactic" scores better with raters than one that says "possibly
phishing, I'm about 60% on this," *even when 60% is the correct state of knowledge.*

That is the crux: **RLHF systematically trains confidence away from calibration.** A generative
model's self-reported `"confidence": 0.95` is a stylistic artifact of what confident text looks
like. It is not a measurement.

## RLCD optimises for the number being true

**Reinforcement Learning for Calibrated Decisions** replaces the human preference signal with a
scoring rule over outcomes. The model is not rewarded for being liked. It is rewarded for the
probability it emits matching the frequency with which it turns out to be right.

The mechanism is a **proper scoring rule** — Brier score, log loss, or similar. The defining
property of a proper scoring rule is that it is minimised *only* by reporting your true belief.
Overclaiming is penalised. Underclaiming is penalised. Hedging to be safe is penalised.

```text
Brier score for a binary decision:
  B = (p - o)²        where p = predicted probability, o = outcome (0 or 1)

Say 100 events. If you say 0.9 every time and are right 90 times, your
expected score is optimal. Say 0.99 and be right 90 times, and you are
punished for the 10 confident misses far more than you gained on the hits.
```

Under this objective, the model has no incentive to sound sure. Saying `0.62` when you are
62% likely to be right is the *winning* move. The number becomes load-bearing.

## Side by side

| | RLHF | RLCD |
| :--- | :--- | :--- |
| **Reward signal** | Human preference between outputs | Proper scoring rule over real outcomes |
| **Optimises for** | Perceived helpfulness | Probabilistic accuracy |
| **Confidence means** | Stylistic register | Empirical frequency |
| **Failure under uncertainty** | Confident fabrication | A low number |
| **Output space** | All token sequences | Your enumerated categories |
| **Needs labelled outcomes?** | No — preferences suffice | Yes — this is the expensive part |
| **Good at** | Language, reasoning, generation | Decisions, routing, scoring |

## Why you cannot prompt your way across

This is the question everyone asks, so here it is directly: *can't I just tell an LLM to be
well-calibrated?*

You can ask. It will not work reliably, for three reasons:

1. **The prompt is fighting the gradient.** Calibrated-sounding hedging was penalised across
   the whole of post-training. A system message is a weak nudge against a strong prior.
2. **There is no measurement in the loop.** The model produces the *token* `0.87` because 0.87
   is a plausible-looking confidence value in that context. Nothing consulted an internal
   probability, because the thing being sampled is a text distribution, not a belief.
3. **It is not stable.** Prompt phrasing, ordering, and temperature all move the number.
   Anything that moves with phrasing is not a measurement.

There is real research on eliciting better-calibrated verbal probabilities from LLMs, and it
does improve things. But "improved" is not the same as "you can set a threshold on it and page
someone at 3am." If you need the second one, you need a model trained for it.

## What this costs

RLCD is not free lunch. Its requirements are genuinely harder in one specific way:

**RLHF needs preferences. RLCD needs ground truth.** You cannot train a calibrated decision
model on "which of these looks better" — you need to know what actually happened. That means
labelled outcomes, at scale, in the domain. It is why decision-native models tend to be strong
in domains with abundant labelled history (security, fraud, moderation, classification) and
weaker in domains where ground truth is contested or slow to arrive.

It is also why **calibration is domain-bound**. A model calibrated on English support tickets is
not automatically calibrated on Portuguese ones. Verify on your own distribution before you
trust the number — [here is how](/concepts/calibrated-confidence/).

## Next

- [Understanding Calibrated Confidence](/concepts/calibrated-confidence/) — read and verify the number
- [The Zero Hallucination Guarantee](/concepts/zero-hallucination/) — the other architectural consequence
