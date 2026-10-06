---
title: 'System One vs. System Two AI: A Mental Model for Developers'
description: Fast reflexes versus slow deliberation, the architectural split every AI developer needs to understand.
sidebar:
  label: System One vs. System Two
  order: 1
---

For the last few years, the AI industry has been obsessed with building a better brain. We got models
that pass the bar exam, write poetry and reason through logic puzzles.

But as developers, we quickly learned a painful truth: **we don't always need a brain. Most of the
time, we need a reflex.**

Borrowing from Daniel Kahneman's *Thinking, Fast and Slow*, AI systems are splitting into two kinds.
To build reliable AI workflows, you need to know which one you're holding.

## The problem: we're using System Two for everything

Generative models (large language models) are **System Two** AI: built for slow, deliberate,
step-by-step reasoning. Ask one a question and it writes the answer one token at a time. It's trained,
largely on human feedback, to be helpful and conversational.

**The developer experience with System Two:**

- **Latency:** seconds. You're waiting on a token stream.
- **Output:** strings: Markdown, prose, or JSON you hope is formatted correctly.
- **Failure mode:** hallucination. It generates strings, so it can generate strings that aren't true,
  or aren't valid.
- **Best for:** chat, pair programming, drafting, complex multi-step reasoning.

Using a System Two model for high-volume routing, security filtering or real-time moderation is like
hiring a philosophy professor to sort your mail: too slow, too expensive, and prone to overthinking.

### What that actually costs you

The cost isn't only the API bill. It's the code you write around the model:

```python title="the_tax_you_pay.py"
res = llm.chat(
    messages=[
        {"role": "system", "content": 'You are a classifier. Respond with ONLY valid JSON matching '
                                      '{"category": "a"|"b"|"c", "confidence": number}. '
                                      "Do not include markdown fences. Do not explain."},
        {"role": "user", "content": text},
    ],
    temperature=0,
)
try:
    parsed = json.loads(strip_fences(res.text))
except json.JSONDecodeError:
    parsed = retry_with_stricter_prompt(text)            # sometimes twice

if parsed.get("category") not in ALLOWED:
    parsed = {"category": "unknown", "confidence": 0}    # it invented a fourth category again
```

Every line after the API call defends against the model's output format. None of it is business
logic. And `parsed["confidence"]` is a number the model *wrote down*. It isn't a measurement of
anything.

## The solution: System One models

A System One model is the reflex. It gives up token generation entirely: you give it your program's
state and typed questions, and it scores every possible answer against that state in one pass,
returning a probability for each. [Kenning](https://huggingface.co/systemonedev/kenning-large-v0.5)
(open, 435M parameters) and Cloudflare's Clef (open, 9B) run on your own hardware. TypeSafe's Jev is
a hosted one. [Compare them](/start/engines/).

They're trained for a different goal: a **well-calibrated probability**, not a helpful sentence. A
model whose "0.9" is right about 90% of the time is a model you can put a threshold on.
[How that training works](/concepts/how-models-are-trained/).

**The developer experience with System One:**

- **Latency:** tens to hundreds of milliseconds. Kenning answers in 33–88 ms per request on one
  consumer GPU.
- **Output:** typed answers, with a probability for every option.
- **Failure mode:** being wrong or unsure, and telling you how unsure. It can't invent an answer
  outside your options.
- **Best for:** agent guardrails, request routing, alert triage, moderation, high-volume pipelines.

## The developer's cheat sheet

| | System Two (generative) | System One (decision) |
| :--- | :--- | :--- |
| **Examples** | GPT, Claude, Llama, Qwen | Kenning, Clef, Jev |
| **Output** | streaming tokens (strings) | typed answers and probabilities |
| **Latency** | seconds | tens to hundreds of milliseconds |
| **Trained for** | helpfulness and reasoning | calibrated probabilities |
| **Malformed or invented output** | possible | impossible: always one of your options |
| **Wrong answers** | possible | possible, with a probability you can act on |
| **The code you write** | prompts and parsers | thresholds and `if` statements |

## Stop parsing. Start routing.

You no longer need prompts begging the model to `ONLY RETURN VALID JSON AND NOTHING ELSE`. You hand
the model your data, ask typed questions, and get probabilities back. When the model is well
calibrated on your data, and you [check that it is](/concepts/calibrated-confidence/), answers it gives
at 0.98 are right about 98% of the time.

That lets you write ordinary deterministic code around your AI:

```python title="the_system_one_paradigm.py"
r = client.system_one(state={"request": raw_request},
                      questions={"sqli": Noul("Is this request a SQL injection attempt?")})

if r.nouls["sqli"].noul >= 0.95:
    firewall.block(request.ip)
else:
    route_to_analyst(raw_request)
```

Read that block again and notice what's *missing*: no prompt, no parser, no retry, no validation of
the answer, no temperature. The model's output is already the shape your program needs.

## The part where we're honest with you

This is a mental model, not a religion. Three caveats are worth holding onto:

**System Two isn't going away, and shouldn't.** Anything whose output is genuinely *generated* (a
reply, a summary, a refactor) belongs to System Two. The argument here is about putting each
architecture where it fits.

**"No hallucination" is a narrower claim than it sounds.** A model that can only return one of your
options can't invent a fake citation. It can absolutely pick the wrong option.
[We spell this out](/concepts/zero-hallucination/), because overclaiming it is how teams get burned.

**Calibration is a property to verify, not assume.** It holds on the distribution the model was
calibrated for. Point it at inputs unlike anything it has seen and the numbers drift.
[Measuring it yourself](/concepts/calibrated-confidence/) takes an afternoon and is worth it.

## Next

- [The wire format](/concepts/wire-format/): exactly what you send and get back
- [The fuzzy if-statement](/cookbook/fuzzy-if-statement/): the code pattern this enables
- [Is System One right for my problem?](/start/when-to-use/): an honest decision tree
