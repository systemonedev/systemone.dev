---
title: Structured State Ingestion
description: Turning logs, records, and events into input a decision model evaluates well.
sidebar:
  label: Structured State Ingestion
  order: 3
---

Your production state is structured: rows, objects, events, nested records. The model evaluates
unstructured state. The translation between them is the highest-leverage step in the whole
integration, and the one most teams skip.

Two teams with the same model and the same categories routinely see very different accuracy.
It is almost always this.

## The principle

You are not writing a prompt. You are **selecting and presenting evidence.** Everything in the
input should be something a competent human would look at to make the same decision. Everything
else is noise competing for the model's attention.

## Do not dump JSON

```javascript title="dont.js"
// Weak: keys, nesting, and internal identifiers the decision does not depend on.
const decision = await jev.evaluate({
  input: JSON.stringify(order),
  categories: ['fraud', 'legitimate'],
});
```

Raw `JSON.stringify` gives the model punctuation, schema noise, UUIDs, timestamps in epoch
milliseconds, and internal flags — all weighted the same as the signal.

```javascript title="do.js"
// Strong: labelled, human-readable, signal only.
function serializeOrder(order) {
  return [
    `Order total: $${order.total}`,
    `Account age: ${daysSince(order.account.createdAt)} days`,
    `Previous orders: ${order.account.orderCount}`,
    `Billing country: ${order.billing.country}`,
    `Shipping country: ${order.shipping.country}`,
    `Billing and shipping match: ${order.billing.country === order.shipping.country}`,
    `Payment method: ${order.payment.type}`,
    `Card country: ${order.payment.issuerCountry}`,
    `Email domain: ${order.account.email.split('@')[1]}`,
    `Items: ${order.items.map((i) => i.name).join(', ')}`,
    `Order placed: ${describeTime(order.createdAt)}`,
  ].join('\n');
}

const decision = await jev.evaluate({
  input: serializeOrder(order),
  categories: ['fraud', 'legitimate', 'unclear'],
});
```

## The rules

### 1. Label every field

`Account age: 3 days` carries the meaning. A bare `3` does not.

### 2. Compute the comparison, don't make the model do it

If the signal is "billing and shipping countries differ," state that as a boolean. Derived
features are cheap for you and eliminate a step the model would otherwise have to infer.

```javascript
`Billing and shipping match: ${b.country === s.country}`,
`Unusually large vs account average: ${order.total > account.avgOrderValue * 5}`,
`First order from this device: ${!account.knownDevices.includes(deviceId)}`,
```

### 3. Make time relative

`1710432000` and `2024-03-14T16:00:00Z` both require the model to know "now." Convert:

```javascript
function describeTime(ts) {
  const mins = (Date.now() - new Date(ts)) / 60_000;
  if (mins < 60) return `${Math.round(mins)} minutes ago`;
  if (mins < 1440) return `${Math.round(mins / 60)} hours ago`;
  return `${Math.round(mins / 1440)} days ago`;
}
```

`3 minutes ago, at 04:12 local time` is a fraud signal. An epoch timestamp is not.

### 4. Drop what the decision does not depend on

UUIDs, internal flags, schema versions, audit columns. If a human reviewer would not look at
it, it is noise. This also keeps your input small, which keeps it fast.

### 5. Truncate long fields from both ends

For long text, the beginning and end usually carry the signal — the middle is filler. Keep both:

```javascript
function truncate(text, max = 2000) {
  if (text.length <= max) return text;
  const half = Math.floor(max / 2) - 20;
  return `${text.slice(0, half)}\n\n[... ${text.length - max} characters omitted ...]\n\n${text.slice(-half)}`;
}
```

Naive head-truncation is how injected instructions in a message footer get silently dropped.

### 6. Mark untrusted content explicitly

When the input contains user-controlled text, fence it so the boundary is unambiguous:

```javascript
const input = [
  `Sender: ${email.from}`,
  `Sender domain age: ${domainAgeDays} days`,
  `SPF: ${email.spf}  DKIM: ${email.dkim}`,
  `Links point to: ${extractDomains(email.body).join(', ')}`,
  '',
  '--- BEGIN UNTRUSTED MESSAGE BODY ---',
  truncate(email.body),
  '--- END UNTRUSTED MESSAGE BODY ---',
].join('\n');
```

A decision model has no instruction channel to hijack — see
[Zero Hallucination](/concepts/zero-hallucination/) — but the fence still helps it treat that
region as content being described rather than context to reason from.

## Worked example: an HTTP request

```javascript title="serialize-request.js"
export function serializeRequest(req) {
  const lines = [
    `Method: ${req.method}`,
    `Path: ${req.path}`,
    `Source IP reputation: ${req.ipReputation ?? 'unknown'}`,
    `Requests from this IP in last minute: ${req.rateCount}`,
    `Authenticated: ${Boolean(req.userId)}`,
    `User agent: ${req.headers['user-agent'] ?? '(none)'}`,
  ];

  if (req.query && Object.keys(req.query).length) {
    lines.push('', 'Query parameters:');
    for (const [k, v] of Object.entries(req.query)) {
      lines.push(`  ${k} = ${truncate(String(v), 500)}`);
    }
  }

  if (req.body) {
    lines.push('', '--- BEGIN REQUEST BODY ---', truncate(stringify(req.body), 1500), '--- END REQUEST BODY ---');
  }

  return lines.join('\n');
}
```

Note what is absent: request IDs, trace headers, cookies unrelated to auth, content-length. None
of it informs "is this an injection attempt."

## Keep serialization pure and tested

Serialization is ordinary code. Test it like ordinary code, and snapshot it so you notice when
it changes:

```javascript title="serialize.test.js"
it('flags a country mismatch', () => {
  const out = serializeOrder(fixtures.mismatchedCountries);
  expect(out).toContain('Billing and shipping match: false');
});

it('never leaks a full card number', () => {
  expect(serializeOrder(fixtures.withCard)).not.toMatch(/\d{13,19}/);
});

it('is stable', () => {
  expect(serializeOrder(fixtures.standard)).toMatchSnapshot();
});
```

That second test matters. **Serialization is a data egress point.** Everything you put in the
input goes to the model provider — audit it for PII, secrets, and card data deliberately, and
redact at the serializer rather than hoping upstream did it.

## Version your serializer

When you change serialization, you change the question. Accuracy will move, and you need to
know why six weeks later:

```javascript
export const SERIALIZER_VERSION = 'order-v3';

await auditLog.write({
  serializerVersion: SERIALIZER_VERSION,
  categories: CATEGORIES,
  decision,
});
```

Without this, a model swap and a serializer change look identical in your metrics.

## Next

- [The Fuzzy If-Statement](/cookbook/fuzzy-if-statement/) — what to do with the decision
- [Data Engineering project](/projects/data-engineering/) — this pattern at pipeline scale
