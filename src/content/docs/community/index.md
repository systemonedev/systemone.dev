---
title: Community
description: What SystemOne.dev is for, who runs it, and how to get involved.
sidebar:
  order: 0
  label: Overview
---

SystemOne.dev is the open community hub for developers building with System One decision models. It's
run by the maintainers of [SystemOne Builder](https://github.com/systemonedev/systemone-builder) and the
[Kenning](https://huggingface.co/systemonedev) models, and it's open to every engine that speaks the
System One format.

## What we're building

Models that return typed decisions instead of generated text are a real shift, with almost no shared
engineering literature and, until recently, no open models. Every team is rediscovering the same
patterns, making the same threshold mistakes and learning the same lessons about drift on their own.

We're fixing both: the knowledge written down once, here, and the models open, so anyone can run, study
and improve them.

## Our stance

**Open.** The site, the client, the Builder, Kenning's weights, its training recipe and the benchmark
suites are all open source. If we claim a number, you can reproduce it.

**Honest about limits.** Every page that makes a strong claim also says where it breaks down. Kenning's
benchmarks include [where it loses](/start/engines/). "No hallucination" is
[carefully bounded](/concepts/zero-hallucination/#what-does-not-disappear). Calibration is something you
[verify](/concepts/calibrated-confidence/), not something you trust. We'd rather be useful than
impressive.

**Engine-neutral.** Code here runs on Kenning, Clef and Jev. We maintain Kenning, and we say so; pages
about other engines are welcome.

**Not anti-LLM.** Generative models are extraordinary at generation. The argument here is about routing
work to the right kind of model, and most real systems need both.

**Practical over theoretical.** If a page can't show you code you could actually run, it probably
doesn't belong here.

## Get involved

- **[Discussions](https://github.com/systemonedev/systemone-builder/discussions)**: questions, ideas,
  show-and-tell. The best place to start.
- **[Contributing](/community/contributing/)**: add or fix a page, a dataset, a benchmark or code
- **[Roadmap](/community/roadmap/)**: what's planned, and where help is most useful
- **[Issues](https://github.com/systemonedev/systemone-builder/issues)**: bugs in the Builder, Kenning or
  the client. Site issues go to [the site's repository](https://github.com/systemonedev/systemone.dev/issues).
- **[Blog](/blog/)**: release notes, results and community write-ups

## Good first contributions

The highest-value things you can do, roughly in order:

1. **A benchmark from your own workload.** Real accuracy, calibration and latency numbers on real data
   are the scarcest resource in this whole space.
2. **A labelled benchmark suite.** A few dozen hand-labelled, permissively licensed examples from a
   domain we don't cover. It makes every model better measured, and Kenning better trained.
3. **A pattern that failed.** Negative results are underrated and nobody publishes them.
4. **A domain we don't cover.** Fintech, healthcare intake, logistics, ad review. The patterns
   generalise; the specifics don't, and the specifics are what people need.

## Code of conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
Be respectful and constructive, and keep criticism about the work. Report problems privately to
**systemonedev@gmail.com**.
