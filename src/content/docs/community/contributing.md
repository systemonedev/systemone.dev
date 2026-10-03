---
title: Contributing
description: How to add or improve a page on SystemOne.dev, and how to contribute to Kenning and SystemOne Builder.
sidebar:
  order: 1
---

Everything here is open source, and every kind of contribution counts: a typo fix, a page, a benchmark
suite, a bug report, a model improvement.

| You want to | Go to |
| :--- | :--- |
| Fix or add a page on this site | [systemonedev/systemone.dev](https://github.com/systemonedev/systemone.dev) (this page) |
| Improve the Builder, Kenning's training or the `systemone` client | [systemonedev/systemone-builder](https://github.com/systemonedev/systemone-builder): see its [CONTRIBUTING.md](https://github.com/systemonedev/systemone-builder/blob/main/CONTRIBUTING.md) |
| Ask a question or propose an idea | [Discussions](https://github.com/systemonedev/systemone-builder/discussions) |
| Report a security problem | privately: [security policy](https://github.com/systemonedev/systemone-builder/blob/main/SECURITY.md) |

## Quick fix

Every page has an **Edit page** link at the bottom. It opens the file in GitHub's editor, and committing
opens a pull request. Use it for typos, broken links and small corrections: no local setup needed.

## Local setup

```bash
git clone https://github.com/systemonedev/systemone.dev.git
cd systemone.dev
npm install
npm run dev          # http://localhost:4321
```

```bash
npm run build        # type-checks content and builds; run before opening a PR
npm run linkcheck    # fails on any broken internal link or heading anchor
```

Node 20 or newer.

## Adding a page

Drop a Markdown file into the right directory. The sidebar picks it up automatically.

```text
src/content/docs/
├── start/         Orientation, quickstart, engines
├── concepts/      Mental models: the "unlearning" section
├── cookbook/      Integration patterns
├── projects/      End-to-end builds
├── community/     This section
└── blog/          Dated posts
```

Every page needs frontmatter:

```markdown
---
title: Handling Backpressure in Decision Pipelines
description: One sentence, used for search results and social cards.
sidebar:
  label: Backpressure      # optional: shorter text for the sidebar
  order: 5                 # optional: position within the section
---
```

A blog post needs a date and authors instead:

```markdown
---
title: We Ran 2M Decisions Through Three Models
description: Latency and calibration results from a production moderation workload.
date: 2026-11-10
authors:
  - your-github-handle
excerpt: What we measured, on what data, and what surprised us.
tags: [benchmarks, moderation]
---
```

## Style

**Write for someone shipping this on Thursday.** Concrete over abstract. If you can show code, show code.

**Code must run.** Use the [`systemone-client`](https://pypi.org/project/systemone-client/) client and the real wire
format: `client.system_one(state=..., questions=...)`. Run your snippet against a Kenning server or
`Kenning.from_pretrained` before you submit it. Mark elisions (`...`) clearly rather than pretending a
snippet is complete. Example outputs must be real outputs, with the model named.

**Say where it breaks.** Every strong claim is paired with its limits. A page that only lists advantages
reads as marketing, and review will ask for the caveats.

**Numbers need a source.** "Kenning answers in 33–88 ms" is fine because it says what was measured, on
what. "40% cost reduction" needs to say on what workload, measured how. If it's your own data, say so:
that makes it more valuable, not less.

**Engine-neutral.** Write the architecture so it transfers between engines. When something is specific to
one engine, say so.

**Link sideways.** Concepts link to the Cookbook pattern that applies them; Cookbook pages link to the
concept that justifies them. The cross-links are much of the value.

## What we're looking for

Highest value first:

1. **Benchmarks on real workloads**: accuracy, calibration, latency, cost, and what the data was.
2. **Labelled benchmark suites**: small, hand-labelled, openly licensed sets for a domain. They go into
   the Builder's `systemone bench`, so every engine can be measured on them.
3. **Negative results**: patterns that failed in production, and why.
4. **New domains**: fintech, healthcare intake, logistics, ad review, legal intake.
5. **Operational write-ups**: what drift actually looked like, how you caught it, what you changed.

## What we'll push back on

- Marketing for any engine, including ours, or benchmarks with no stated method
- "No hallucination" claims without the [bounds](/concepts/zero-hallucination/)
- "LLMs are obsolete" framing: they aren't, and it costs everyone credibility
- Thresholds presented as universal constants
- Example outputs that weren't produced by a real model

## Review

Pull requests get a review within a few days. Expect comments, usually asking for a caveat, a source or a
link to a related page. It isn't gatekeeping; it's what keeps this site worth reading.

By contributing, you agree your work is published under the site's licences:
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) for content and MIT for code. Everyone
taking part follows the [code of conduct](/community/#code-of-conduct).
