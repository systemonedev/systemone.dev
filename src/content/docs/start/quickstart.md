---
title: 'Quickstart: your first decision'
description: Get a typed, calibrated decision back from a real piece of input in about five minutes.
sidebar:
  order: 2
---

The goal: send one messy string to a System 1 model and get back a typed decision you can
branch on. No prompt engineering, no JSON parsing.

:::note[Vendor neutrality]
This quickstart uses Jev because it is the most complete System 1 model available today. Any
decision-native model with a categorical evaluation endpoint works the same way — the shape of
the code is the point, not the SDK.
:::

## 1. Install

```bash
npm install @typesafe/jev
```

```bash title="Set your key"
export JEV_API_KEY="sk-..."
```

## 2. Evaluate one input

```javascript title="quickstart.js"
import { Jev } from '@typesafe/jev';

const jev = new Jev({ apiKey: process.env.JEV_API_KEY });

const decision = await jev.evaluate({
  input: "URGENT: your account will be closed. Verify at http://secure-login.example.co/verify",
  categories: ['phishing', 'legitimate', 'spam'],
});

console.log(decision);
```

You get back a typed object, not a string:

```json
{
  "category": "phishing",
  "confidence": 0.97,
  "scores": {
    "phishing": 0.97,
    "spam": 0.021,
    "legitimate": 0.009
  },
  "latency_ms": 71
}
```

Three things to notice:

1. **`category` is one of the categories you passed.** It cannot be anything else. There is no
   universe in which the model returns `"phishing!"` or `` "```json\n{...}" ``.
2. **`confidence` is calibrated.** Across a large sample of decisions scored at `0.97`, roughly
   97% are correct. That is a property of the training objective, not a vibe. See
   [Calibrated Confidence](/concepts/calibrated-confidence/).
3. **`latency_ms` is double digits.** No token stream to wait on.

## 3. Branch on it

This is the part that changes how you write code. You are not writing a prompt — you are
writing an `if`.

```javascript title="triage.js"
const THRESHOLD = 0.95;

async function triage(email) {
  const decision = await jev.evaluate({
    input: `${email.subject}\n\n${email.body}`,
    categories: ['phishing', 'legitimate', 'spam'],
  });

  if (decision.confidence < THRESHOLD) {
    return { action: 'escalate', reason: 'low_confidence', decision };
  }

  switch (decision.category) {
    case 'phishing':
      return { action: 'quarantine', decision };
    case 'spam':
      return { action: 'junk_folder', decision };
    case 'legitimate':
      return { action: 'deliver', decision };
  }
}
```

Note the shape: **confidence gates first, category routes second.** Getting that order right
is the single most common correction new System 1 developers need. The
[fuzzy if-statement](/cookbook/fuzzy-if-statement/) page covers why.

## 4. Do it at volume

Decision models evaluate in parallel rather than sequentially, so batching is cheap:

```javascript title="batch.js"
const decisions = await jev.evaluateBatch({
  inputs: emails.map((e) => `${e.subject}\n\n${e.body}`),
  categories: ['phishing', 'legitimate', 'spam'],
});

const quarantined = decisions.filter(
  (d) => d.category === 'phishing' && d.confidence > 0.95,
);
```

## Where to go next

- **Set your thresholds honestly** → [Calibrated Confidence](/concepts/calibrated-confidence/)
- **Feed it real production state** → [Structured State Ingestion](/cookbook/structured-state-ingestion/)
- **Put it in front of an agent** → [Agent Guardrails & Verification](/cookbook/agent-guardrails/)
- **Build the whole thing** → [The Zero-Latency AI Firewall](/projects/cybersecurity/)
