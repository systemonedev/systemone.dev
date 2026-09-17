---
title: Contributing
description: How to add or improve a page on SystemOne.dev.
sidebar:
  order: 1
---

Every page here is a Markdown file in a public repo. If you can write a PR, you can contribute.

## Quick fix

Every page has an **Edit page** link at the bottom. It opens the file directly in GitHub's
editor, and committing opens a PR. Use it for typos, broken links, and small corrections — no
local setup needed.

## Local setup

```bash
git clone https://github.com/systemone-dev/systemone.dev.git
cd systemone.dev
npm install
npm run dev          # http://localhost:4321
```

```bash
npm run build        # type-checks content and builds; run before opening a PR
```

Node 20 or newer.

## Adding a page

Drop a Markdown file into the right directory. The sidebar picks it up automatically.

```text
src/content/docs/
├── start/         Orientation and quickstart
├── concepts/      Mental models — the "unlearning" section
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
date: 2026-09-10
authors:
  - your-github-handle
excerpt: What we measured, on what data, and what surprised us.
tags: [benchmarks, moderation]
---
```

## Style

**Write for someone shipping this on Thursday.** Concrete over abstract. If you can show code,
show code.

**Say where it breaks.** Every strong claim on this site is paired with its limits. A page that
only lists advantages reads as marketing and will get review comments asking for the caveats.

**Vendor-neutral by default.** Examples use Jev for consistency, but write the *architecture* so
it transfers. Avoid framing that only makes sense for one vendor's API.

**Numbers need a source.** "70ms" is fine as the widely-cited figure for this class of model.
"40% cost reduction" needs to say on what workload, measured how. If it is your own data, say so
— that makes it more valuable, not less.

**Link sideways.** Concepts should link to the Cookbook pattern that applies them; Cookbook
pages should link to the concept that justifies them. The cross-links are much of the value.

**Code should run.** Use real syntax, real error handling, and realistic variable names. Mark
elisions with a comment rather than pretending the snippet is complete.

## What we are looking for

Highest value first:

1. **Benchmarks on real workloads** — latency, accuracy, calibration, cost. Say what the data
   was.
2. **Negative results** — patterns that failed in production and why. Genuinely scarce.
3. **Other frameworks** — anything that widens this beyond one implementation.
4. **New domains** — fintech, healthcare, logistics, ad review, legal intake.
5. **Operational write-ups** — what drift actually looked like, how you caught it, what you
   changed.

## What we will push back on

- Vendor marketing, or benchmarks with no stated methodology
- Claims of zero hallucination without the [bounds](/concepts/zero-hallucination/)
- "LLMs are obsolete" framing — they are not, and it costs us credibility
- Confidence thresholds presented as universal constants

## Review

PRs get a review within a few days. Expect comments — usually asking for a caveat, a source, or
a link to a related page. It is not gatekeeping; it is the thing that keeps this site worth
reading.

By contributing you agree your work is published under the same license as the site
([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) for content, MIT for code).
