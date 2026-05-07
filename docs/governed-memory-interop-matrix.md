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

## Canonical Fixture Expectations

Every backend pair or consumer path should be exercised with a canonical
fixture set containing:

1. a plain `v1.0` `KnowledgeEntry`
2. a `v1.2` `KnowledgeEntry` with `governance`
3. a `v1.2` `KnowledgeEntry` with extended `provenance`
4. a `v1.2` `KnowledgeStore` containing mixed entries
5. a `GET /v1/capabilities` response advertising governance support

## Invariants To Verify

- `governance.sensitivity_class` survives export/import unchanged
- `governance.labels` survive export/import unchanged
- `provenance.sources[]` survives export/import unchanged
- unsupported governance fields are tolerated rather than rejected
- capabilities discovery accurately reflects governance and provenance support
- lossy behavior is documented explicitly when a backend drops unsupported
  fields instead of preserving them opaquely

## Pairings

| Producer | Consumer | Direction type | Required checks | Status |
|----------|----------|----------------|-----------------|--------|
| `cosmictron` | `kizuna-mem` | backend -> backend | governance, provenance, capabilities | planned |
| `kizuna-mem` | `cosmictron` | backend -> backend | governance, provenance, capabilities | planned |
| `cosmictron` | `ultra` | backend -> backend | governance, provenance, capabilities | planned |
| `ultra` | `cosmictron` | backend -> backend | governance, provenance, capabilities | planned |
| `kizuna-mem` | `ultra` | backend -> backend | governance, provenance, capabilities | planned |
| `ultra` | `kizuna-mem` | backend -> backend | governance, provenance, capabilities | planned |
| `cosmictron` | `toraeru` | backend -> integrator | capabilities, fixture consumption | planned |
| `kizuna-mem` | `toraeru` | backend -> integrator | capabilities, fixture consumption | planned |
| `ultra` | `toraeru` | backend -> integrator | capabilities, fixture consumption | planned |

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
