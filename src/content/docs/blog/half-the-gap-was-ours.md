---
title: 'Half the Gap Was Ours: What Happened When We Benchmarked Kenning Against Someone Else'
description: Our own benchmark said the new model was better. A third-party benchmark said it was worse. Diagnosing that recovered about half of what looked like a model-quality gap, and the follow-up experiment was more interesting than the fix.
date: 2026-10-13T09:00:00Z
authors:
  - david
excerpt: We published Kenning v0.6 because it beat v0.5 on the benchmark we wrote. The first time we ran a benchmark we did not write, v0.6 scored worse than the model it replaced. Three of the defects turned out to be ours, not the model's.
tags: [kenning, benchmarks, engineering]
---

We publish Kenning as an open System One model, and for months we measured it with a benchmark we
wrote ourselves. That was the mistake. This post is what we found when we stopped.

## The reality check

Our general suite is 1,328 held-out items across seven families of state. By that measure v0.6 was a
clear improvement on v0.5: macro accuracy 0.753 against 0.653. We published it, wrote the docs around
it, and called it the more accurate model.

Then we ran [WorkflowEvals](https://huggingface.co/datasets/typesafe/workflowevals) for the first
time. It is TypeSafe's benchmark, Apache-2.0, built from realistic business documents: invoices,
agent traces, customer service conversations, security alerts. Each question is scored against an
OpenAI plus Anthropic consensus label. We had never trained on it and never will, which is the whole
point of using it.

v0.6 scored **0.463**. A hosted competitor scored **0.800**. And v0.5, the model v0.6 was supposed to
replace, scored **0.552**.

So our newer model was worse on a benchmark we did not write, while being 0.10 better on the one we
did. That is the textbook signature of overfitting to your own evaluation, and it meant our headline
metric had stopped predicting anything useful.

The obvious response was to go and get more training data. We are glad we did not, because almost
half of that gap turned out to be our own code.

## Killing the comfortable explanations first

**It was not the context window.** v0.6 reads 2,048 tokens and the invoice states run to about 6,200,
so truncation was the first suspect. But v0.6 scored 0.479 on items that fit inside the window and
0.479 on items that did not. Identical. The customer service states are around 240 tokens, they fit
trivially, and we were still near chance on them.

**It was not inverted labels.** When a binary classifier scores below chance, check whether you wired
the polarity backwards. AUC on the yes/no questions came out at 0.598: above 0.5, so correctly
oriented, just carrying very little signal.

**It was not calibration.** Our probabilities were crushed into a band around 0.5, which looks like a
temperature problem. It is not, because for a two-option question the temperature cancels out of the
comparison. Accuracy cannot change no matter what you set it to.

What remained was that the model genuinely could not separate these items, which raised the question
of why, given it does fine on our own structured tasks.

## Defect one: the two things being compared were the same string

Kenning answers a yes/no question by building two hypotheses and comparing them. A question can carry
a criteria object describing each answer:

```json
{"true":  "The customer states someone else made a charge or accessed the account.",
 "false": "The customer recognises the activity, or reports nothing unauthorised."}
```

Our renderer flattened that object into one blob and pasted it into *both* hypotheses. So the model
was asked to compare these two strings:

```
...did not make or authorize? (true: someone else made a charge | false: reports nothing
unauthorised.) Answer: yes.

...did not make or authorize? (true: someone else made a charge | false: reports nothing
unauthorised.) Answer: no.
```

They are byte-identical apart from "yes." and "no.". The most discriminating field in the question
contributed exactly zero signal, and the "yes" hypothesis literally contained the description of the
false case.

With nothing else to go on, the model matched the question topically against the state. Our favourite
example: asked whether the customer reported an *unauthorised* charge, on a conversation purely about
a late desk delivery, it answered 0.588 yes. The words "charge" and "340 dollars" appear in the
conversation, so it said yes. The competitor said 0.0009.

The fix is three lines of judgement rather than cleverness. A yes/no question is a two-option choice,
and our multi-option code already gave each option its own description. Yes takes the true side, no
takes the false side.

## Defect two: options were judged on different evidence

Our tokeniser trims the state to whatever room each hypothesis leaves. That sounds reasonable until
you notice that the options within a single question have different lengths.

On the invoice questions, option descriptions quote the invoice lines back at you, so they run from
240 to 552 tokens. Against an 8,516 token state with a 2,048 token budget, two things follow. Only 21
percent of the document survived. And the budget varied by up to 199 tokens between options, so the
longest-described option saw less of the invoice than the shortest one.

Then we softmax over those scores and call it a probability distribution. We were comparing numbers
computed over different evidence, which is unsound whatever the accuracy happens to be, and it made
the answer depend on how verbosely each option was worded. The budget is now computed once per
question from the longest hypothesis, so every option is scored against identical state.

## Defect three: we graded one question type against itself

Score questions return an expected value over ordered levels, so a model torn between level 1 and
level 3 outputs something near 2. Our benchmark graded these by rounding that expected value and
checking for an exact match.

An engine that returns a hard integer level loses nothing to rounding. We lose plenty. On the same
items: 0.267 for us by rounding, 0.400 by taking the most likely level. The hosted engine scored
0.400 either way.

So the metric was quietly penalising the one engine that answers with a distribution, which is the
entire design goal of the project. Our multi-option questions were already graded by most-likely
answer, so making score consistent with them was worth 0.017 to us and exactly zero to an engine that
emits integers.

## Where that landed

WorkflowEvals, 240 items, no retraining and no new data:

| | original | after defect one | after all three |
|---|---|---|---|
| v0.5 | 0.552 | 0.599 | **0.625** |
| v0.6 | 0.463 | 0.533 | **0.575** |
| hosted reference | 0.800 | 0.800 | 0.800 |

The gap went from 0.337 to 0.175. On our own suite the same changes moved v0.6 from 0.753 to 0.761,
with gains only in the two families whose states are long enough for the budget to matter and every
other family unchanged, which is the fingerprint you want from a change like this.

## The part we are least comfortable with

AUC on the yes/no questions went from 0.598 to 0.576. It did not improve. Ranking quality was
basically unchanged.

What actually happened is that the whole distribution shifted downward, and since only 35 percent of
these labels are yes, shifting toward no agrees with the base rate more often. So a real part of that
accuracy gain is base-rate alignment rather than new discriminative power. The old rendering was
provably degenerate, so the fixes are right regardless, but it would be dishonest to present this as
having taught the model anything.

## The follow-up was more interesting than the fix

One detail from defect one nagged at us. The fix was safe to ship immediately because **not one of
the 27,144 yes/no questions in our training data carried a criteria field at all.** The model had
never seen the pattern. So we had fixed the rendering of a field the model had never learned to read.

That looked like an obvious win: generate training data where the criteria are present, retrain, and
the model learns to use the most discriminating part of the question. We did exactly that. Sixty
percent of yes/no questions in the new dataset carry criteria, built from the label descriptions the
generators already held, with the rest left bare so the model would not come to depend on a field our
own suites never send. Everything else was held constant, down to a question-type mix within 0.2
percent of the previous dataset.

The headline result was flat. WorkflowEvals macro 0.575, exactly what the previous model scored.

Underneath, it was not flat at all:

| | v0.6 | v0.7 (criteria) |
|---|---|---|
| yes/no accuracy at 0.5 | 0.658 | 0.627 |
| **yes/no at its best threshold** | 0.702 | **0.720** |
| yes/no AUC | 0.593 | **0.622** |

**The training worked.** Discrimination improved, and at its own best threshold the new model is the
strongest we have measured. It is the decision boundary that throws the gain away: the conventional
0.5 cut costs it 0.093, because this model's best cut is at 0.621.

And then the detail that explains the whole thing. The optimal yes/no threshold is **0.621 on
WorkflowEvals, where every question carries criteria, and 0.152 on our general suite, where none do.**
Opposite directions. Training with criteria on some questions and not others taught the model two
different probability scales, one per input regime, and no single threshold serves both.

We checked the obvious culprit and ruled it out: criteria presence does not leak the answer. The
yes-rate is 0.456 with criteria and 0.458 without, a difference of 0.002. The mixed design did not
correlate presence with the label. The model simply learned two output scales for two input
distributions.

So we are not shipping it. v0.5 remains the strongest as served on WorkflowEvals, v0.6 on our own
suite.

## One thing this exposed in our own tooling

For a two-option question, `p >= 0.5` is equivalent to `score_yes >= score_no`, which is
temperature-invariant. So `systemone calibrate` can improve expected calibration error but **can never
move a yes/no decision boundary.** Correcting boundary placement needs a per-question-type bias term
alongside temperature, and we do not have one.

That matters well beyond this experiment. Any model whose boundary drifts is currently uncorrectable
by our calibration machinery, and we found that out by accident.

## What we would tell anyone building this

**Evaluate on something you did not build.** Our own benchmark rewarded a change that made the model
worse in the wild, and we would not have known for as long as we kept grading our own homework.

**Below chance means mis-wired, not weak.** A genuinely weak model lands at chance. Below it is a
clue, and AUC is the cheap way to tell an inverted signal from an absent one.

**Look at the exact bytes your model sees.** Not the config, not the schema, the literal string. We
found the largest defect in this project by printing two hypotheses next to each other and noticing
they were the same.

**Check your metric is not measuring your own output convention.** If one engine returns
distributions and another returns hard labels, at least one of your metrics is probably unfair, and it
is probably unfair to you.

**Separate discrimination from threshold placement before concluding anything.** A flat headline
number hid both a real improvement and a real regression in our case. AUC and a threshold sweep cost
nothing and tell you which one you are looking at.

Every fix above is in
[SystemOne Builder](https://github.com/systemonedev/systemone-builder), and the benchmark suites are
open so you can run them yourself. The uncomfortable version of this story is the useful one: a model
that beats our own benchmark and loses someone else's was worth finding out about now, rather than
after someone else ran the comparison for us.
