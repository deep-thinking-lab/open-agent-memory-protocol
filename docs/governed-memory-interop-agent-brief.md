# Governed-Memory Interop Brief for Backend Implementers

**Status:** Working brief
**Related issue:** [#18](https://github.com/deep-thinking-llc/open-agent-memory-protocol/issues/18)
**Companion script:** [`scripts/interop-roundtrip.sh`](../scripts/interop-roundtrip.sh)
**Companion doc:** [`docs/governed-memory-interop-matrix.md`](./governed-memory-interop-matrix.md)

This document is the brief to hand to a backend implementer (or an agent
acting on a backend repo) so they can wire OAMP v1.2 governed-memory interop
without having to reverse-engineer the spec.

## Goal

Make this backend pass the canary round-trip:

```
scripts/interop-roundtrip.sh \
  --producer-url <this-backend> \
  --consumer-url <peer-backend>
```

The script must exit 0 in both directions (this-as-producer and
this-as-consumer).

## What the canary does

1. Validates `spec/v1.2/examples/knowledge-store-interop.json` — a 3-entry
   store containing one v1.0 entry, one v1.2 governed entry, and one
   provenance-only entry.
2. `POST <producer>/v1/import` with the fixture.
3. `POST <producer>/v1/export` with `{"user_id":"user-alice-123"}` and saves
   the response.
4. `POST <consumer>/v1/import` with that producer export.
5. `POST <consumer>/v1/export` with the same export request.
6. `GET /v1/capabilities` from both backends.
7. Diffs the producer and consumer exports keyed by entry id, comparing
   `id`, `oamp_version`, `governance`, and `provenance`.
8. If there is drift, dropped fields are reconciled against the consumer's
   `/v1/capabilities`. Drift is allowed only when the consumer advertises the
   gap (e.g. `governance.labels_supported = false`).

## Invariants this backend must uphold

- `POST /v1/import` accepts a `KnowledgeStore`, persists every entry, and
  returns HTTP 201 with an `id_mappings` array. It must not silently drop
  entries with unknown optional fields.
- `POST /v1/export` accepts `{"user_id": "..."}` and returns the user's
  full `KnowledgeStore`. Order is not required to match.
- Optional `governance` and `provenance` fields on a `KnowledgeEntry` must
  round-trip unchanged when this backend supports them. If the backend does
  not support a field, it must EITHER preserve it opaquely OR drop it AND
  advertise the drop in `/v1/capabilities`.
- Entries that arrive without `governance` (e.g. the v1.0 entry in the
  fixture) must come back without `governance`. Do not stamp default
  sensitivity classes or labels.
- `/v1/capabilities` must accurately describe what this backend supports.
  At minimum:
  - `governance.supported: bool`
  - `governance.labels_supported: bool`
  - `governance.handling_supported: bool`
  - `governance.extended_provenance_supported: bool`

  False is a valid honest answer; lying is not.

## Deliverables

1. Code changes so `/v1/import`, `/v1/export`, and `/v1/capabilities` meet
   the invariants above.
2. A CI job in this backend's repo that runs the canary against this
   backend and a reference peer. Use the OAMP reference server
   (`reference/server/`) as the peer if no real partner is wired up.
3. Document any intentional lossy behaviour in this backend's README and
   confirm `/v1/capabilities` reflects it.

## Non-goals

- Do not implement v1.3 enforcement (signed grants, governed retrieval).
  That is a separate track.
- Do not invent withheld/redacted result documents. That is the v2.0 RFC
  track and is intentionally out of scope here.
- Do not modify the OAMP spec repo or its fixtures from this backend's
  repo. If the spec or fixtures appear wrong, file an issue against
  `open-agent-memory-protocol` instead.

## Reporting back

Once green, post the producer/consumer URLs you tested, the resulting
`diff-report.txt`, and both `/v1/capabilities` documents to issue #18 so the
matrix row can be flipped from `planned` to `passing` (or
`lossy: <field> — declared in capabilities`).
