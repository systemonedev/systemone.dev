---
title: Structured State
description: Turning logs, records and events into state a System One model evaluates well.
sidebar:
  label: Structured State
  order: 3
---

Your production state is structured: rows, objects, events, nested records. A System One request
takes that structure directly (`state` can be a JSON object), but *which* structure you send is the
highest-leverage step in the whole integration, and the one most teams skip.

Two teams with the same model and the same questions routinely see very different accuracy. It's
almost always this.

## The principle

You're not writing a prompt. You're **selecting and presenting evidence.** Everything in the state
should be something a competent person would look at to make the same decision. Everything else is
noise competing for the model's attention, and for its token budget: Kenning reads 512 tokens per
(state, option) pair and cuts off the rest.

## Don't dump the whole record

```python title="dont.py"
# Weak: keys, nesting and internal identifiers the decision doesn't depend on.
r = client.system_one(state=order.to_dict(), questions={"fraud": Noul("Is this order fraudulent?")})
```

A raw record gives the model UUIDs, epoch timestamps, internal flags and schema noise, all weighted
the same as the signal, and it can push the signal past the token limit.

```python title="do.py"
# Strong: descriptive keys, derived signals, nothing else.
def order_state(order) -> dict:
    return {
        "order_total_usd": order.total,
        "account_age_days": days_since(order.account.created_at),
        "previous_orders": order.account.order_count,
        "billing_country": order.billing.country,
        "shipping_country": order.shipping.country,
        "billing_and_shipping_match": order.billing.country == order.shipping.country,
        "payment_method": order.payment.type,
        "card_issuer_country": order.payment.issuer_country,
        "email_domain": order.account.email.split("@")[1],
        "items": [i.name for i in order.items],
        "placed": describe_time(order.created_at),
    }

r = client.system_one(state={"order": order_state(order)}, questions={
    "fraud": Noul("Is this order fraudulent?"),
})
```

## The rules

### 1. Make keys say what they mean

The model reads the keys. `"account_age_days": 3` carries the meaning; `"aa": 3` doesn't. Include
units in the name (`_days`, `_usd`).

### 2. Compute the comparison, don't make the model do it

If the signal is "billing and shipping countries differ", send that as a boolean. Derived features
are cheap for you and remove a step the model would otherwise have to infer. Arithmetic and dates are
exactly where models of this size are weakest.

```python
derived = {
    "billing_and_shipping_match": b.country == s.country,
    "unusually_large_vs_account_average": order.total > account.avg_order_value * 5,
    "first_order_from_this_device": device_id not in account.known_devices,
}
```

### 3. Make time relative

`1710432000` and `2024-03-14T16:00:00Z` both require the model to know what "now" is. Convert:

```python
from datetime import datetime, timezone

def describe_time(ts: datetime) -> str:        # ts must be timezone-aware
    mins = (datetime.now(timezone.utc) - ts).total_seconds() / 60
    if mins < 60:
        return f"{round(mins)} minutes ago"
    if mins < 1440:
        return f"{round(mins / 60)} hours ago"
    return f"{round(mins / 1440)} days ago"
```

"3 minutes ago, at 04:12 local time" is a fraud signal. An epoch timestamp isn't.

### 4. Leave out what you don't know

If a field is missing, omit it. Don't fill it with a placeholder like `"(untagged)"`, `"unknown"` or
`"N/A"`: the model reads every value as evidence. Measured with `kenning-large-v0.4` on a marketplace
listing: adding `"seller_tagged_category": "(untagged)"` to the state moved an iPhone from
*electronics* to *other* (0.60) and an oak dining table from *home & garden* to *other* (0.82). Without
that one field, both were classified correctly.

```python
state = {"title": row.title, "description": row.description}
if row.seller_category:                 # only when there's something to say
    state["seller_tagged_category"] = row.seller_category
```

The exception is when absence *is* the signal. "This request has no user agent" says something about
a bot, so say it explicitly: `"has_user_agent": False`.

### 5. Drop what the decision doesn't depend on

UUIDs, internal flags, schema versions, audit columns. If a person reviewing the case wouldn't look at
it, it's noise. Smaller state is also faster.

### 6. Truncate long text from both ends

For long text, the beginning and end usually carry the signal. Keep both, so a footer isn't silently
cut off:

```python
def truncate(text: str, max_chars: int = 1500) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2 - 20
    return f"{text[:half]}\n[... {len(text) - max_chars} characters omitted ...]\n{text[-half:]}"
```

### 7. Keep untrusted content in its own field

When the state contains user-controlled text, put it in a clearly named field, separate from the facts
you computed:

```python
state = {
    "sender": email.sender,
    "sender_domain_age_days": domain_age_days,
    "spf": email.spf, "dkim": email.dkim,
    "link_domains": extract_domains(email.body),
    "untrusted_message_body": truncate(email.body),
}
```

A System One model has no instruction channel to hijack (see
[what "no hallucination" means](/concepts/zero-hallucination/)), but text inside the body can still
try to sway the answer. Facts you computed yourself, like domain age, SPF and link domains, are much
harder for an attacker to fake than words in the body.

## Worked example: an HTTP request

```python title="request_state.py"
def request_state(req) -> dict:
    state = {
        "method": req.method,
        "path": req.path,
        "requests_from_this_ip_last_minute": req.rate_count,
        "authenticated": req.user_id is not None,
        "has_user_agent": "user-agent" in req.headers,     # absence is a signal: say so explicitly
    }
    if req.ip_reputation:                                  # unknown: leave it out (rule 4)
        state["source_ip_reputation"] = req.ip_reputation
    if "user-agent" in req.headers:
        state["user_agent"] = req.headers["user-agent"]
    if req.query:
        state["query_parameters"] = {k: truncate(str(v), 300) for k, v in req.query.items()}
    if req.body:
        state["untrusted_request_body"] = truncate(stringify(req.body), 1000)
    return state
```

Note what's absent: request ids, trace headers, cookies unrelated to auth, content-length. None of it
informs "is this an injection attempt?"

## Keep the state builder pure and tested

The function that builds the state is ordinary code. Test it like ordinary code:

```python title="test_order_state.py"
def test_flags_a_country_mismatch():
    assert order_state(fixtures.mismatched_countries)["billing_and_shipping_match"] is False

def test_never_leaks_a_card_number():
    assert not re.search(r"\d{13,19}", json.dumps(order_state(fixtures.with_card)))
```

That second test matters. **The state is a data egress point.** With a hosted engine, everything in
it leaves your network. Audit it for personal data, secrets and card numbers deliberately, and redact
in the state builder rather than hoping upstream did. A local model like Kenning keeps the data on
your machine, which is one reason to choose one.

## Version your state builder

When you change the state, you change the question. Accuracy will move, and six weeks later you'll
need to know why:

```python
STATE_VERSION = "order-v3"

audit_log.write({"state_version": STATE_VERSION, "model": r.model, "answers": r.raw["answers"]})
```

Without this, a model swap and a state change look identical in your metrics.

## Next

- [The fuzzy if-statement](/cookbook/fuzzy-if-statement/): what to do with the answer
- [Data engineering project](/projects/data-engineering/): this pattern at pipeline scale
