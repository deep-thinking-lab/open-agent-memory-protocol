# Open Agent Memory Protocol — v2.0 RFC Draft for Withheld/Redacted Results

**Status:** Draft RFC seed  
**Date:** 2026-05-07  
**Authors:** Deep Thinking LLC  
**Related issue:** `#16`

---

## 1. Problem

OAMP `v1.x` can standardize governed-memory metadata, but it cannot yet
standardize what happens when a caller is not allowed to see a memory.

Today, backends may need to express:

- the memory exists,
- the memory matched the query,
- the caller is not allowed to see the content,
- the backend either omitted it or returned a redacted stub,
- the backend may know a structured withholding reason.

Current `v1.x` contracts do not model that cleanly because:

- `KnowledgeEntry.content` is required and non-empty,
- list/search responses are arrays of `KnowledgeEntry`,
- stream payloads for creates and updates assume full entries.

That means portable withheld-result semantics require a new response model and
therefore belong to a major-version track.

---

## 2. Goals

- standardize a portable model for withheld or redacted results
- preserve privacy by default
- allow audited/admin surfaces to receive explicit withholding information
- support mixed result sets containing visible entries and withheld stubs
- work across REST, export/import, and streaming surfaces

## 3. Non-Goals

- standardize cross-backend authorization policy languages
- force every backend to emit withheld stubs rather than omitting results
- define tenant-specific sensitivity labels beyond the existing `v1.2`
  governed-memory metadata

---

## 4. Candidate Directions

### Option A: New response envelope

Keep `KnowledgeEntry` mostly intact and introduce a new envelope such as:

```json
{
  "result_type": "visible",
  "entry": { "...KnowledgeEntry..." }
}
```

or

```json
{
  "result_type": "withheld",
  "entry_id": "...",
  "withholding_reason": "sensitivity_class",
  "sensitivity_class": "confidential"
}
```

Pros:

- preserves the meaning of `KnowledgeEntry`
- works for mixed result sets
- cleanest path for REST and streaming symmetry

Cons:

- requires new response and event shapes
- clients must handle envelopes instead of raw entry arrays

### Option B: Major-version `KnowledgeEntry` expansion

Allow `KnowledgeEntry.content` to become nullable or optional and add fields
like `withheld`, `withholding_reason`, and `redacted_fields`.

Pros:

- fewer wrapper types

Cons:

- weak separation between visible and withheld documents
- easier for clients to misuse partially redacted entries
- more ambiguity for exports and mixed search results

### Option C: New withheld document type

Introduce a separate document type such as `withheld_knowledge_entry`.

Pros:

- explicit and strongly typed

Cons:

- clunkier mixed result sets
- more duplication across REST and streaming payload schemas

## 5. Recommendation

Use **Option A: a new response/event envelope**.

Why:

- it preserves `KnowledgeEntry` as a fully visible document,
- it models omission vs explicit withholding cleanly,
- it works naturally for list/search/export/streaming,
- it avoids overloading core entry semantics with policy state.

---

## 6. Proposed Direction

### 6.1 New result envelope

Introduce a `MemoryResult`-style envelope with two initial variants:

- `visible`
- `withheld`

### 6.2 Withheld payload

The withheld variant should carry only non-sensitive metadata:

- stable entry identifier when safe to reveal
- standardized `withholding_reason`
- optional `sensitivity_class`
- optional vendor metadata

### 6.3 Default behavior

The protocol should support both backend behaviors:

- silent omission
- explicit withheld stub

But the default interoperability model should remain:

- omission for general callers
- explicit stubs only where the surface or caller is authorized for that mode

### 6.4 Compatibility

This is a `v2.0` change because:

- REST list/search responses need new result arrays or envelopes
- streaming payloads need new event payload types
- export/import semantics may need explicit handling for withheld data

---

## 7. Open Questions

- Should `withholding_reason` be a closed enum, extensible enum, or vendor-safe
  namespace?
- When should `entry_id` itself be hidden?
- Should export ever include withheld stubs, or should export remain
  owner-scoped only?
- How should omission vs explicit withholding be advertised in capabilities?

---

## 8. Immediate Next Steps

- use this draft as the starting artifact for issue `#16`
- keep `v1.2` governance work unblocked
- feed any real backend requirements from `cosmictron`, `kizuna-mem`, `ultra`,
  and `toraeru` into the envelope design before freezing `v2.0`
