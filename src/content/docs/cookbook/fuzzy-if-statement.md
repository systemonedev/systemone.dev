---
title: The "Fuzzy" If-Statement
description: Routing logic built on confidence bands — the foundational System 1 code pattern.
sidebar:
  label: The Fuzzy If-Statement
  order: 1
---

Every System 1 integration is, at bottom, one pattern: a typed decision, a confidence gate, and
a branch. Get the shape right once and every subsequent integration is a variation.

## The pattern

```javascript title="fuzzy-if.js"
const decision = await jev.evaluate({
  input: rawState,
  categories: ['approve', 'reject', 'review'],
});

// 1. Gate on confidence FIRST.
if (decision.confidence < THRESHOLD) {
  return escalate(rawState, decision);
}

// 2. Then branch on category.
switch (decision.category) {
  case 'approve': return approve();
  case 'reject':  return reject();
  case 'review':  return queueForReview();
}
```

## The ordering mistake

This is the single most common bug in new System 1 code:

```javascript title="wrong.js"
// WRONG — the confidence check is trapped inside one branch.
if (decision.category === 'fraud' && decision.confidence > 0.95) {
  blockTransaction();
} else {
  allowTransaction();   // a 0.94-confidence fraud signal silently becomes "allow"
}
```

A decision of `{ category: 'fraud', confidence: 0.94 }` — a strong fraud signal — falls into
`else` and gets approved. The `else` branch has quietly become a dumping ground for *both*
"confidently fine" and "alarmingly uncertain," which are opposite situations.

```javascript title="right.js"
// RIGHT — uncertainty is its own branch, evaluated before category.
if (decision.confidence < 0.95) {
  return manualReview(transaction, decision);  // 0.94 fraud lands here
}
return decision.category === 'fraud' ? blockTransaction() : allowTransaction();
```

**Rule: uncertainty is a first-class outcome, not a modifier on another outcome.**

## Three bands

Two bands (automate / escalate) is the minimum. Three is better, because "uncertain" and
"nothing fits" need different handling:

```javascript title="three-band.js"
const BANDS = {
  AUTO: 0.95,   // derived from cost of error — see /concepts/calibrated-confidence/
  FLOOR: 0.60,  // below this the model is signalling "I have no idea"
};

export async function route(item) {
  const decision = await jev.evaluate({
    input: serialize(item),
    categories: CATEGORIES,
  });

  metrics.histogram('decision.confidence', decision.confidence, {
    category: decision.category,
  });

  if (decision.confidence >= BANDS.AUTO) {
    return { action: ACTIONS[decision.category], decision, automated: true };
  }

  if (decision.confidence >= BANDS.FLOOR) {
    return { action: 'human_review', decision, automated: false };
  }

  // Not a hard case — likely an input your categories do not cover.
  metrics.increment('decision.below_floor', { category: decision.category });
  return { action: 'triage', decision, automated: false, reason: 'below_floor' };
}
```

## Per-category thresholds

Cost of error is rarely uniform. Wrongly approving a refund is not the same as wrongly denying
one. Encode that:

```javascript title="thresholds.js"
// Asymmetric by design: destructive actions need more certainty than safe ones.
const THRESHOLDS = {
  block:      0.99,  // false positive = a blocked legitimate user
  quarantine: 0.95,
  flag:       0.85,
  allow:      0.80,  // the safe default; a false positive here costs little
};

const DEFAULT_THRESHOLD = 0.95;

function isAutomatable(decision) {
  return decision.confidence >= (THRESHOLDS[decision.category] ?? DEFAULT_THRESHOLD);
}
```

Keep these in config, not scattered through the codebase. You will tune them, and you want the
diff to be one file.

## Always include an escape category

If reality contains a case your list does not, the model must still pick one of yours — often
with misleadingly high confidence. Give it somewhere to go:

```javascript
const CATEGORIES = [
  'billing_question',
  'technical_issue',
  'account_access',
  'other',            // the escape hatch
];
```

Then alert on its share of traffic. A rising `other` rate is the earliest signal that your
taxonomy has drifted out of date — long before accuracy visibly drops.

## Composing decisions

Chain cheap decisions before expensive work rather than asking one model one enormous question:

```javascript title="pipeline.js"
export async function handleMessage(msg) {
  // Cheap gate: is this even actionable? (~70ms)
  const relevance = await jev.evaluate({
    input: msg.text,
    categories: ['actionable', 'noise'],
  });
  if (relevance.category === 'noise' && relevance.confidence > 0.9) {
    return { action: 'drop' };
  }

  // Narrower question, only for what survived. (~70ms)
  const intent = await jev.evaluate({
    input: msg.text,
    categories: ['refund', 'bug_report', 'feature_request', 'other'],
  });
  if (intent.confidence < 0.9) return { action: 'human_review', intent };

  // The expensive path, now taken rarely. (~2000ms)
  if (intent.category === 'bug_report') {
    return { action: 'draft_reply', body: await llm.chat({ /* ... */ }) };
  }

  return { action: ROUTES[intent.category] };
}
```

Two 70ms calls that prevent one 2,000ms call is a good trade roughly every time.

## Testing it

The nice property of this pattern: your routing logic is deterministic and testable in
isolation. Test the routing with fixtures, and evaluate the model separately.

```javascript title="route.test.js"
import { describe, it, expect } from 'vitest';
import { classify } from './route.js';

const d = (category, confidence) => ({ category, confidence });

describe('routing bands', () => {
  it('automates above the threshold', () => {
    expect(classify(d('fraud', 0.99)).action).toBe('block');
  });

  it('escalates a high-signal but sub-threshold decision', () => {
    // The regression test for the ordering bug above.
    expect(classify(d('fraud', 0.94)).action).toBe('human_review');
  });

  it('triages below the floor', () => {
    expect(classify(d('fraud', 0.4)).action).toBe('triage');
  });

  it('never auto-approves on an uncertain fraud signal', () => {
    for (let c = 0; c < 0.95; c += 0.01) {
      expect(classify(d('fraud', c)).action).not.toBe('allow');
    }
  });
});
```

Note that `classify` takes a decision object rather than calling the model. Keep the model call
at the edge and the branching pure — you get fast tests and a function you can reason about.

## Next

- [Handling the 70ms Loop](/cookbook/the-70ms-loop/) — keeping the call itself fast
- [Structured State Ingestion](/cookbook/structured-state-ingestion/) — what to put in `input`
