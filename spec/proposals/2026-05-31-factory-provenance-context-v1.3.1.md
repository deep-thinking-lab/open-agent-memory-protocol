# Proposal: OAMP Factory / Delegated Provenance Context (v1.3.1)

**Status:** Proposal draft
**Target version:** v1.3.1 (additive over v1.0 / v1.1 / v1.2 / v1.3)
**Date:** 2026-05-31
**Authors:** Jonathan Conway (Deep Thinking)
**Repository:** `github.com/deep-thinking-lab/open-agent-memory-protocol`
**Depends on:** `spec/v1.3/oamp-v1.3-draft.md` (§4.1 claims, §4.3 provenance binding)
**Related:** `spec/proposals/2026-05-31-grant-issuer-and-mediation-v1.3.1.md`

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## Abstract

OAMP v1.3 §4.3 binds a write to the calling agent via
`entry.source.agent_id == oamp_agent_id`. That is sufficient when the agent is a
stable, standalone identity. It is **not** sufficient for **delegated, ephemeral
agents** that act on behalf of a larger unit of work and exist only for the
duration of that work.

This proposal adds OPTIONAL grant claims that carry the **delegation context** of
such an agent — the task it was spawned for, and any grouping above that task —
and a SHOULD that the backend stamp this context onto written entries so
knowledge remains attributable to the originating work, not just to an ephemeral
agent id that no longer exists. All additions are backward-compatible.

## 1. Motivation

A common governed pattern: a planner decomposes a goal into tasks; each task is
executed by a short-lived agent provisioned for it; the agent is revoked when
the task ends. Knowledge those agents write outlives them.

Binding such a write to `oamp_agent_id` alone is weak provenance:

- the agent id is **ephemeral** — after revocation it resolves to nothing;
- it loses the **delegation chain** — which task, and which grouping of tasks,
  produced the knowledge;
- it prevents useful queries like "show everything learned during task X."

The originating context (`task`, and an optional parent grouping) is known at
grant-issuance time. Carrying it on the grant lets the backend record durable,
queryable provenance without inventing a parallel side-channel.

## 2. Non-goals

- This proposal does not define the *semantics* of the grouping above a task
  (campaign, mission, session, run — deployment's choice). It standardizes only
  the **carriage** of opaque identifiers.
- It does not change read filtering or sensitivity semantics.
- It does not require backends to index by these fields (a SHOULD, not a MUST,
  for queryability).

## 3. Grant claim additions (§4.1 delta)

The following OPTIONAL claims extend the v1.3 §4.1 grant claim set:

| Claim | Requirement | Description |
|-------|-------------|-------------|
| `oamp_task_id` | MAY | Identifier of the unit of work the agent was provisioned to perform. |
| `oamp_context_id` | MAY | Identifier of an OPTIONAL grouping above the task (campaign / mission / run). Opaque to OAMP. |

Both are opaque strings. They carry the delegation context; they do **not**
grant any additional read/write authority (labels and sensitivity remain the
sole authority claims, per v1.3 §4–§5).

> Deployments MAY use additional vendor-prefixed claims for richer context
> (e.g. `oamp_x_cell_id`). Only `oamp_task_id` and `oamp_context_id` are
> standardized here.

## 4. Write-time provenance stamping (§4.3 delta)

When a write occurs under a grant carrying these claims, a v1.3.1 backend
SHOULD record them in the entry's provenance so attribution survives the agent:

```json
{
  "source": {
    "session_id": "sess-cell-42",
    "timestamp": "2026-05-31T12:00:00Z",
    "agent_id": "cell-agent-42"
  },
  "provenance": {
    "sources": [
      {
        "session_id": "sess-cell-42",
        "timestamp": "2026-05-31T12:00:00Z",
        "agent_id": "cell-agent-42",
        "task_id": "task-7",
        "context_id": "mission-3"
      }
    ]
  }
}
```

> `session_id` and `timestamp` are REQUIRED on both `source` and each
> `provenance.sources[*]` entry by the v1.2/v1.3 `knowledge-entry` schema; they
> are shown here so the example validates. `agent_id`, `task_id`, and
> `context_id` are the additive fields.

- The backend SHOULD copy `oamp_task_id` → `provenance.sources[*].task_id` and
  `oamp_context_id` → `provenance.sources[*].context_id` for the entry written
  under that grant.
- The existing §4.3 binding is unchanged: the backend MUST still verify
  `entry.source.agent_id == oamp_agent_id` when `source.agent_id` is present.
- `task_id` / `context_id` on `provenance.sources[*]` are descriptive
  attribution, not authority; backends MUST NOT use them to widen access.

## 5. Queryability (optional)

A backend MAY support filtering reads by `task_id` / `context_id` (subject to the
normal v1.3 §5.1 read grant — provenance filters narrow, they never widen).
Backends that support it SHOULD advertise it under the v1.3 governance
enforcement block (v1.3 §6 — `capabilities.governance.enforcement`, with a
top-level `oamp_version`):

```json
{
  "oamp_version": "1.3.1",
  "capabilities": {
    "governance": {
      "enforcement": {
        "provenance_query": ["task_id", "context_id"]
      }
    }
  }
}
```

## 6. Required schema & reference-type updates

The v1.3 `knowledge-entry` schema defines `$defs.provenance_source` (and
`source`) with **`additionalProperties: false`**, so `task_id` / `context_id`
are rejected today. This proposal is therefore **not** purely descriptive — it
requires, normative for v1.3.1:

1. **JSON Schema:** add OPTIONAL `task_id` and `context_id` (string) to the
   v1.3.1 `knowledge-entry` schema's `provenance_source` definition. Without
   this, a writer following the §4 SHOULD emits a **schema-invalid** entry.
2. **Reference types:** add the same OPTIONAL fields to the `oamp-types`
   provenance-source shape (Rust/TS/Python/Go/Elixir) so the additive carriage
   round-trips, mirroring how v1.2/v1.3 governance metadata is parsed additively.

`session_id` / `timestamp` remain REQUIRED on `provenance_source`; the new
fields are additive and OPTIONAL.

## 7. Backwards compatibility

- **v1.3.0 backends:** ignore the new claims; provenance is recorded as today
  (agent_id only). Safe.
- **v1.0–v1.2 clients:** unaffected; the claims are optional and additive.
- **Entries written without the claims:** unchanged shape — no `task_id` /
  `context_id` keys appear.
- Composes with the issuer/mediation proposal: a mediator that mints the grant
  is the natural place to populate these context claims.

## 8. Conformance summary

A v1.3.1 backend that supports factory provenance SHOULD:

- record `oamp_task_id` / `oamp_context_id` onto `provenance.sources[*]` on write;
- preserve the v1.3 §4.3 `source.agent_id` binding;
- treat the context fields as descriptive only (never authority-widening);
- if it offers provenance queries, advertise `governance.provenance_query`.

## 9. Open questions

1. Flat claims (`oamp_task_id`, `oamp_context_id`) vs a single nested
   `oamp_provenance` object. This draft chooses flat claims for JWT-friendliness.
2. Whether `context_id` should allow a list (multi-level grouping) rather than a
   single opaque id.
3. Interaction with v2.0 provenance chains, if any.

## References

- `spec/v1.3/oamp-v1.3-draft.md` — §4.1 grant claims, §4.3 provenance binding, §6 capabilities
- `spec/v1.2/oamp-v1.2.md` — governance metadata, provenance shape
- Companion: `2026-05-31-grant-issuer-and-mediation-v1.3.1.md`
