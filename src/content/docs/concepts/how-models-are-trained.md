---
title: How System One Models Are Trained
description: Cross-encoders, calibration by temperature, and distillation from a larger teacher. Why System One models behave so differently from chat models, using Kenning as the worked example.
sidebar:
  label: How They're Trained
  order: 5
---

You don't need to train a model to use one. But knowing how they're built explains their behaviour:
why the probabilities can be trusted, where they stop being trustworthy, and what you can do about
it. This page uses [Kenning](https://huggingface.co/systemonedev/kenning-large-v0.4) as the example,
because its whole recipe is open. Other engines differ in the details.

## The architecture: score every option, generate nothing

Kenning is a **cross-encoder**, a transformer that reads two texts together and outputs a score. For
each question, every possible answer becomes a short statement read against the state:

| Question | Statements scored against the state | Answer |
| :--- | :--- | :--- |
| noul | "`<instructions>` Answer: yes." / "... no." | P(yes) |
| choice | "`<instructions>` Answer: `<option>`. `<description>`" per option | probability per option |
| score | "`<instructions>` Answer: `<level>`." per level | probability per level |

All the statements of all the questions in a request are scored in one batch. The scores become
probabilities with a softmax. Nothing is generated, so nothing can come out except your options.

Kenning starts from a model already trained for *natural-language inference*: deciding whether one
text supports another. That's why it can answer questions it was never trained on, zero-shot, and why
fine-tuning teaches it the System One format quickly.

## Training for calibration, not helpfulness

A chat model is tuned to produce answers people like. A System One model is tuned so that its
probabilities **match how often it's right**. Two things do that:

**1. The loss rewards honest probabilities.** Training minimises cross-entropy between the model's
distribution and the target distribution. A model that says 0.99 and is wrong is punished far more
than one that said 0.6. Over thousands of examples, that pushes the numbers toward observed
frequencies.

**2. Temperatures are fitted after training.** Neural networks are usually overconfident. After
training, Kenning holds out 10% of its data and fits one *temperature* per question type: a single
number that softens or sharpens every distribution (`softmax(scores / T)`), chosen to make held-out
probabilities as honest as possible. `kenning-large-v0.4` uses T = 1.22 for nouls and choices and 1.16
for scores. It's cheap, it doesn't change which answer wins, and it's the reason "0.9" means
something.

The catch, and you can't skip it: **calibration is fitted on the training distribution.** On data
unlike it, the numbers drift. That's why every page on this site tells you to
[measure on your own data](/concepts/calibrated-confidence/#verifying-calibration-yourself).
SystemOne Builder can refit the temperatures on a few hundred of your labelled examples.

## Distillation: learning from a larger teacher

Labelled data says *what* the answer is. It doesn't say how sure to be. A **teacher model** can.
Kenning v0.4 was trained on targets that average each human label with the probabilities of
Cloudflare's Clef, a model about 20 times larger:

```text
target = 0.5 × label + 0.5 × teacher's probabilities
```

A "soft" target like `{phishing: 0.8, spam: 0.2}` teaches the student that an example is genuinely
ambiguous, which is exactly what calibration needs. Teacher and labels also disagree in informative
ways: in Kenning's data, Clef agreed with the labels 96% of the time on product reviews but only 73% on
toxicity labels, which flags noise in those labels.

Only distil from teachers whose terms allow it. Clef is Apache-2.0. TypeSafe's terms forbid training
on Jev's outputs.

## Data: what it learns from

Kenning v0.4's fine-tuning data is permissively licensed or generated, and every source is listed
with its licence in the model card:

- public labelled datasets: natural-language inference (MNLI), customer intents (CLINC), product
  reviews, comment toxicity;
- emails and tasks written by an open LLM from labelled scenarios, including deliberately hard pairs:
  calm, corporate-sounding phishing next to its legitimate twin;
- the same state in several layouts (plain text, headers, nested JSON), so the model learns not to
  depend on formatting.

Benchmark suites are never used for training. That's what makes the
[published numbers](/start/engines/#same-benchmarks-side-by-side) mean something.

## What this means for you

- **The probabilities are only as good as the calibration data was representative.** Check them on
  yours.
- **Good option descriptions help a lot.** The model literally reads "Answer: billing. Charges,
  refunds, invoices": the description is part of what it scores.
- **You can make your own.** SystemOne Builder's Train page builds a dataset, distils from Clef if you
  have it, fine-tunes and calibrates, and its Verify page benchmarks the result. See the
  [Builder on GitHub](https://github.com/systemonedev/systemone-builder).

## Next

- [Understanding calibrated confidence](/concepts/calibrated-confidence/): reading and checking the numbers
- [Engines](/start/engines/): Kenning, Clef and Jev compared
