# Proposal: OAMP Grant Issuer Binding & Mediation Requirement (v1.3.1)

**Status:** Proposal draft
**Target version:** v1.3.1 (additive over v1.0 / v1.1 / v1.2 / v1.3)
**Date:** 2026-05-31
**Authors:** Jonathan Conway (Deep Thinking)
**Repository:** `github.com/deep-thinking-lab/open-agent-memory-protocol`
**Depends on:** `spec/v1.3/oamp-v1.3-draft.md` (§4 grant claims, §5 enforcement)
**Related:** `spec/proposals/2026-05-07-permissioned-memory-v1.3.md`

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## Abstract

OAMP v1.3 (§4) defines agent **grant claims** carried in a JWT or the
`OAMP-Grant` header, and (§5) the backend enforcement rules that apply them.
v1.3 assumes a **two-party** model: the calling agent presents its own grant
directly to the backend.

This proposal adds the **mediated** model: a grant is minted by a **trusted
issuer** (a mediator that sits between agent and backend), and the backend is
configured to **reject grants that do not originate from a trusted issuer** when
a resource requires mediation. It introduces one standard claim (`iss`), one
optional claim (`oamp_mediation_required`), an entry-level `handling` value
(`mediated`), a trusted-issuer backend configuration, and the enforcement and
capability rules that bind them. All additions are backward-compatible.

## 1. Motivation

In governed multi-agent platforms the agent is frequently **not trusted to
self-assert its own grant**. A separate authority evaluates policy, scopes the
grant, and signs it; the memory backend must be able to prove the grant came
from that authority and refuse anything else.

Concretely (the motivating deployment): ephemeral worker agents run inside
isolated cells. A central governor mints a scoped, signed grant per cell and
proxies the agent's memory access. The memory backend must:

1. accept grants **only** from the governor's signing key(s), and
2. **reject** a grant presented directly by a cell (self-issued, or issued by an
   untrusted party), for resources marked as requiring mediation.

v1.3 cannot express this: it has no notion of *who issued* a grant, nor any way
to require mediation. The grant is simply a bearer object the agent holds. This
proposal closes that gap.

## 2. Non-goals

- This proposal does **not** define the mediator's internal policy engine, nor
  how it decides a grant's labels/sensitivity. That is deployment-specific.
- It does **not** mandate a particular PKI, key-distribution, or rotation
  mechanism. It specifies only that the backend holds a set of trusted issuer
  keys and how it uses them.
- It does **not** change the v1.3 claim semantics for read/write labels or
  sensitivity; it composes with them.

## 3. Grant claim additions

### 3.1 `iss` (issuer)

| Claim | Requirement | Description |
|-------|-------------|-------------|
| `iss` | MUST when mediation is required; otherwise MAY | Stable identifier of the authority that minted the grant. Matches a key entry in the backend's trusted-issuer set. |

`iss` reuses the registered JWT `iss` claim ([RFC 7519] §4.1.1). When the grant
is conveyed as the `OAMP-Grant` compact JWS (v1.3 §4.2), `iss` is a claim in the
JWS payload and the JWS signature MUST verify against the key registered for
that issuer.

### 3.2 `oamp_mediation_required`

| Claim | Requirement | Description |
|-------|-------------|-------------|
| `oamp_mediation_required` | MAY | When `true`, signals that this grant is intended for a mediated flow. Informational for clients; backends rely on their own resource policy (§5), not solely on this flag. |

## 4. Backend configuration: trusted-issuer set

A v1.3.1 backend MAY be configured with a **trusted-issuer set**: a mapping from
`iss` value to one or more verifying keys and the permitted signature algorithm
(e.g. `EdDSA`). A backend with a non-empty trusted-issuer set is said to
**support mediation**.

A backend MUST verify the grant's signature against the key registered for the
grant's `iss`. A grant whose `iss` is absent from the set, or whose signature
does not verify under that issuer's key, is **untrusted**.

## 5. Enforcement (normative)

A resource is **mediation-required** if the backend's policy marks it so (for
example, an entry whose `governance.handling` includes `mediated` — §6 — or a
backend operating in mediation-only mode).

For a mediation-required resource, in addition to the v1.3 §5 rules, the backend
MUST:

1. **Reject untrusted grants.** If the grant's `iss` is absent from the
   trusted-issuer set, or its signature does not verify under that issuer's key,
   the request MUST be treated as having **no valid grant**.
2. **Preserve existence hiding** (v1.3 §5.2). On read surfaces, a request with
   no valid grant MUST yield `404 Not Found` for in-scope-by-content but
   unmediated access — never `403` that reveals existence. On write surfaces,
   rejection is `403 Forbidden` (consistent with v1.3 §5.3).
3. Apply this across all enforced surfaces: read (§5.1), existence (§5.2), write
   (§5.3), import (§5.4), export (§5.5), and stream (§5.6).

A backend that does **not** support mediation (empty trusted-issuer set) ignores
`iss` and behaves exactly as v1.3.

## 6. `governance.handling` addition: `mediated`

This proposal adds an OPTIONAL `mediated` token to the entry-level
`governance.handling` set (v1.2 §3.1 / v1.3 §3.3). An entry tagged
`handling: ["mediated"]` is a mediation-required resource per §5: it MUST NOT be
read, written, exported, or streamed except under a grant from a trusted issuer.

Backends that do not support mediation MUST ignore the `mediated` token (it is
descriptive, per the v1.2 handling model), which preserves compatibility.

## 7. Capabilities advertisement

A v1.3.1 backend that supports mediation SHOULD advertise it in the capabilities
document (v1.3 §6):

```json
{
  "governance": {
    "mediation": {
      "supported": true,
      "trusted_issuers": ["ultra"]
    }
  }
}
```

`trusted_issuers` lists issuer identifiers only — never key material.

## 8. Worked example (non-normative)

1. A governor (`iss: "ultra"`) evaluates policy for an ephemeral cell agent and
   mints an `OAMP-Grant` compact JWS: `iss=ultra`, `oamp_agent_id=cell-agent-42`,
   `oamp_read_labels=["project/*"]`, `oamp_sensitivity_max=confidential`,
   `exp=…`. It signs with its EdDSA key and proxies the agent's recall to the
   backend, attaching the header.
2. The backend (trusted-issuer set `{ultra → <key>}`) verifies the JWS against
   the `ultra` key, accepts the grant, and applies §5.1 read filtering.
3. A compromised cell instead contacts the backend **directly** with a grant it
   minted itself (`iss=cell-agent-42`). The backend finds `cell-agent-42` is not
   in its trusted-issuer set → no valid grant → `404` on the read surface. The
   cell cannot escalate by self-issuing.

## 9. Backwards compatibility

- **v1.3.0 backends:** ignore `iss` / `mediated` and enforce as before. Safe.
- **v1.0–v1.2 clients:** unaffected; they neither send `iss` nor target
  mediation-required resources (which are advertised via capabilities).
- **Grants without `iss`:** accepted by non-mediating backends; treated as
  untrusted (no valid grant) only by backends enforcing mediation on the
  targeted resource.
- The `mediated` handling token is additive to an open string set and is ignored
  where unsupported.

## 10. Conformance summary

A v1.3.1 backend claiming **mediation support** MUST:

- maintain a trusted-issuer set and verify grant signatures against it;
- treat grants with absent/untrusted `iss` as having no valid grant on
  mediation-required resources;
- preserve v1.3 §5 enforcement and existence-hiding semantics;
- advertise `governance.mediation` in capabilities.

## 11. Open questions

1. Should `iss` be REQUIRED on *all* v1.3.1 grants (simpler) or only when
   mediation is required (less disruptive)? This draft chooses the latter.
2. Multiple acceptable issuers per resource vs a single backend-wide set.
3. Key rotation: overlap window for an issuer's old/new verifying keys.

## References

- `spec/v1.3/oamp-v1.3-draft.md` — §4 grant claims, §5 enforcement, §6 capabilities
- `spec/v1.2/oamp-v1.2.md` — §3 governance metadata, `handling`
- [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519) — JSON Web Token (`iss`)
- [RFC 7515](https://www.rfc-editor.org/rfc/rfc7515) — JSON Web Signature (compact JWS)
- Companion: `2026-05-31-factory-provenance-context-v1.3.1.md`
