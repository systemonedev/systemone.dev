---
title: The Fast Loop
description: Keeping decision calls genuinely fast. One request for all questions, connection reuse, concurrency, caching, timeouts and graceful degradation.
sidebar:
  label: The Fast Loop
  order: 2
---

A 40 ms model is easy to turn into a 400 ms endpoint. This page is about not doing that.

## Where the time actually goes

On a local Kenning server, the model is most of the time. Over a network, it often isn't:

| Component | Typical | Notes |
| :--- | ---: | :--- |
| Kenning inference, one RTX 3090 | 33–88 ms | grows with state length and the number of options |
| TLS handshake to a hosted engine | 50–100 ms | **eliminated** by connection reuse |
| Network round trip | 1–80 ms | ~1 ms to a local server, more across regions |
| Building the state | 1–30 ms | see [structured state](/cookbook/structured-state-ingestion/) |
| Each extra request | a full round trip | usually avoidable |

The wins are in rows two, four and five, not in the model.

## Ask every question in one request

The single biggest win. Questions in one request are answered in one pass over the state:

```python title="one_request.py"
# SLOW: three requests, three round trips, the state read three times.
safety = client.system_one(state=s, questions={"safe": SAFE})
intent = client.system_one(state=s, questions={"intent": INTENT})
lang = client.system_one(state=s, questions={"lang": LANG})

# FAST: one request.
r = client.system_one(state=s, questions={"safe": SAFE, "intent": INTENT, "lang": LANG})
```

On Kenning, a request with a noul and a four-option choice takes the same 38 ms as the noul alone. As
two requests it's 76 ms.

## Reuse the client

Create one client per process, at module scope, and reuse it. It keeps connections alive, so you pay
for the TCP and TLS setup once instead of on every decision:

```python title="client.py"
import os
from systemone import Client

# Module scope: one client, one connection pool, for the life of the process.
client = Client(os.environ.get("SYSTEMONE_BASE_URL", "http://localhost:8093"), timeout=0.5)
```

:::caution[Serverless]
On Lambda or Vercel Functions, module scope survives between warm invocations but not cold starts.
Create the client at module scope, never inside the handler, so warm requests reuse the pool.
:::

## Run independent requests concurrently

When you have many *different* states to decide on, don't do them one after another:

```python title="concurrent.py"
import asyncio
from systemone import AsyncClient, Noul

async def classify_all(states, concurrency=16):
    sem = asyncio.Semaphore(concurrency)
    async with AsyncClient("http://localhost:8093") as client:
        async def one(s):
            async with sem:
                r = await client.system_one(state=s, questions={"spam": Noul("Is this spam?")})
                return r.nouls["spam"].noul
        return await asyncio.gather(*(one(s) for s in states))
```

A Kenning server answers one request at a time on its GPU, which is what keeps it deterministic, so
concurrency mostly hides network and client overhead. For bulk work, the throughput you can expect is
roughly 1000 ms divided by the per-request latency, per GPU. Run more Kenning replicas to scale out.

## Cache identical requests

The same request always gets the same answer, on the same model and hardware, so caching is safe.
Key on everything that makes up the question:

```python title="cache.py"
import hashlib, json
from cachetools import TTLCache

cache = TTLCache(maxsize=10_000, ttl=15 * 60)

def key(state, questions, model) -> str:
    payload = {"state": state, "questions": {k: q.to_dict() for k, q in questions.items()}, "model": model}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

def system_one_cached(state, questions, model="kenning-large-v0.5"):
    k = key(state, questions, model)
    if k not in cache:
        cache[k] = client.system_one(state=state, questions=questions)
    return cache[k]
```

:::caution[The questions and the model are part of the key]
Caching on the state alone serves an answer to a different question the moment someone rewords one,
or adds an option. Include the model id too, so a model upgrade doesn't serve stale answers.
:::

Hit rates depend on the workload: high for firewall and moderation traffic (repeated payloads, bots),
low for free-form user text. Measure before you assume.

## Timeouts and graceful degradation

A fast model still lives on a network, or on a GPU that can be busy. Decide in advance what your system
does when an answer doesn't arrive. "Wait" is the wrong answer.

```python title="degrade.py"
import httpx
from systemone import SystemOneError

def safe_fraud_check(state) -> float | None:
    try:
        r = client.system_one(state=state, questions={"fraud": FRAUD})   # client timeout: 0.5 s
        return r.nouls["fraud"].noul
    except (httpx.TimeoutException, httpx.TransportError, SystemOneError) as exc:
        metrics.increment("decision.failure", tags={"reason": type(exc).__name__})
        return None                                   # "no answer", not a made-up probability

p = safe_fraud_check(state)
if p is None or 0.02 < p < 0.95:
    manual_review(order)                              # degraded requests take the human path
```

**Choose the fallback per use case, in the safe direction:**

- A **firewall** should fail closed on sensitive routes: block or challenge, don't allow.
- A **moderation queue** should fail open into human review, not auto-publish.
- A **router** should fall back to the default queue, never silently drop.

Returning `None` rather than a fabricated probability means a degraded answer can never be mistaken
for a confident one.

## Add a circuit breaker

When the model is down, a timeout per request is still time wasted. Stop calling:

```python title="breaker.py"
import time

class CircuitBreaker:
    def __init__(self, threshold=5, reset_s=10.0):
        self.threshold, self.reset_s = threshold, reset_s
        self.failures, self.opened_at = 0, 0.0

    @property
    def is_open(self) -> bool:
        if self.failures < self.threshold:
            return False
        if time.monotonic() - self.opened_at > self.reset_s:
            self.failures = 0                 # half-open: let the next call probe
            return False
        return True

    def record(self, ok: bool) -> None:
        if ok:
            self.failures = 0
        else:
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened_at = time.monotonic()
```

With the breaker open, go straight to the fallback. Your p99 stays flat during an outage instead of
pinning at the timeout.

## Measure the right number

Track **p95 and p99, not the mean.** A mean of 40 ms can hide a p99 of 2 seconds, and your users live
in the p99.

```python
metrics.timing("decision.latency_ms", elapsed_ms, tags={"model": r.model})
metrics.histogram("decision.probability", p)
metrics.increment("decision.cache.hit")
metrics.increment("decision.degraded")
```

That last counter is the one to alert on. Silent degradation, where every request quietly takes the
fallback path while your dashboards look fine, is the failure that hurts.

## Next

- [Structured state](/cookbook/structured-state-ingestion/): cheaper, better input
- [Agent guardrails](/cookbook/agent-guardrails/): the latency-critical use case
