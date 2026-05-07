# Governed Memory Interop Matrix

**Status:** Working draft  
**Date:** 2026-05-07  
**Related issue:** `#18`

This document tracks the minimum interop expectations for governed memory
across the current OAMP ecosystem:

- `cosmictron`
- `kizuna-mem`
- `ultra`
- `toraeru`

## Canonical Fixture Pack

Every backend pair or consumer path should be exercised with the same canonical
fixture set:

1. [spec/v1/examples/knowledge-entry.json](../spec/v1/examples/knowledge-entry.json)
2. [spec/v1.2/examples/knowledge-entry-governed.json](../spec/v1.2/examples/knowledge-entry-governed.json)
3. [spec/v1.2/examples/knowledge-entry-provenance.json](../spec/v1.2/examples/knowledge-entry-provenance.json)
4. [spec/v1.2/examples/knowledge-store-interop.json](../spec/v1.2/examples/knowledge-store-interop.json)
5. [spec/v1.2/examples/capabilities-governance.json](../spec/v1.2/examples/capabilities-governance.json)

Validator-ready copies live under `validators/test-fixtures/valid/` for
backends that want to reuse the same files in CI without bespoke setup.

## Invariants To Verify

- `governance.sensitivity_class` survives export/import unchanged
- `governance.labels` survive export/import unchanged
- `provenance.sources[]` survives export/import unchanged
- unsupported governance fields are tolerated rather than rejected
- capabilities discovery accurately reflects governance and provenance support
- lossy behavior is documented explicitly when a backend drops unsupported
  fields instead of preserving them opaquely

## Execution Checklist

For each producer/consumer pair:

1. Validate the fixture pack locally with the repo validator or equivalent.
2. Import `knowledge-store-interop.json` into the producer backend.
3. Export the same user scope from the producer backend.
4. Confirm the exported document still contains:
   - the untouched `v1.0.0` entry
   - the governed `v1.2.0` entry
   - the provenance-only `v1.2.0` entry
5. Import the producer export into the consumer backend.
6. Export the same user scope from the consumer backend.
7. Diff the producer and consumer exports for:
   - `governance.sensitivity_class`
   - `governance.labels`
   - `governance.handling`
   - `provenance.sources`
   - `provenance.derived`
8. Fetch `GET /v1/capabilities` from both backends and record whether:
   - `governance.supported` is accurate
   - `labels_supported` is accurate
   - `extended_provenance_supported` is accurate
   - governance filter keys are advertised truthfully
9. Record any intentional lossy behavior or unsupported fields in the matrix.

## Pairings

| Producer | Consumer | Direction type | Required checks | Status |
|----------|----------|----------------|-----------------|--------|
| `cosmictron` | `kizuna-mem` | backend -> backend | fixture pack, governance, provenance, capabilities | planned |
| `kizuna-mem` | `cosmictron` | backend -> backend | fixture pack, governance, provenance, capabilities | planned |
| `cosmictron` | `ultra` | backend -> backend | fixture pack, governance, provenance, capabilities | planned |
| `ultra` | `cosmictron` | backend -> backend | fixture pack, governance, provenance, capabilities | planned |
| `kizuna-mem` | `ultra` | backend -> backend | fixture pack, governance, provenance, capabilities | planned |
| `ultra` | `kizuna-mem` | backend -> backend | fixture pack, governance, provenance, capabilities | planned |
| `cosmictron` | `toraeru` | backend -> integrator | fixture pack, capabilities, fixture consumption | planned |
| `kizuna-mem` | `toraeru` | backend -> integrator | fixture pack, capabilities, fixture consumption | planned |
| `ultra` | `toraeru` | backend -> integrator | fixture pack, capabilities, fixture consumption | planned |

## Release-Blocking Minimum For `v1.2`

Before calling governed memory interoperable at `v1.2`, the ecosystem should
have at least:

- one automated backend-to-backend round-trip path using the canonical fixtures
- one consumer/integrator path through `toraeru`
- documented handling for any intentional lossy cases

## Notes

- Portable withheld or redacted result semantics remain out of scope here until
  the separate `v2.0` RFC is resolved.
- This matrix should be updated as each backend lands real support or documents
  an intentional gap.
