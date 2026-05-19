# Proposal: OAMP Audit Profile (v1.4 — portable audit, attestation, and compliance reporting)

**Status:** Draft proposal for community review
**Target version:** v1.4 (additive over v1.0 / v1.1 / v1.2 / v1.3)
**Date:** 2026-05-19
**Authors:** Deep Thinking LLC
**Repository:** `github.com/deep-thinking-llc/open-agent-memory-protocol`
**Depends on:** `spec/v1/oamp-v1.md`, `spec/v1.1/oamp-v1.1-draft.md`, `spec/v1.2/oamp-v1.2-draft.md`, `spec/proposals/2026-05-07-permissioned-memory-v1.3.md`
**Related:** `docs/security-guide.md` §5, §8; `spec/v2.0/oamp-v2.0-withheld-results-rfc.md`

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## Abstract

OAMP v1.2 introduced descriptive governance metadata. v1.3 added enforcement
for that metadata via per-agent grants. Neither version specifies how an
external party — an internal auditor, an external assessor under SOC 2 or
ISO 27001, a regulator, a customer's risk team, or a compliance product —
inspects an OAMP backend to verify those properties without being given
unconstrained read access to user data.

This proposal targets v1.4 and defines the **audit profile**: a portable
audit role with its own scope claims, a small family of `/v1/audit/*`
endpoints exposing aggregate inventory, governance posture, audit-log
events, erasure metrics, and active-grant summaries, and a signed
attestation envelope (JWS, RFC 7515) over every response so reports can
be archived as tamper-evident evidence. Default audit access is
**metadata-only**: aggregate counts, governance distributions, retention
ages, and event logs. Entry content is opt-in via a separate
user-authorised scope, time-bounded, and itself audit-logged.

The proposal is strictly additive under v1.0 §10.3. v1.0, v1.1, v1.2,
and v1.3 documents and clients remain wire-compatible. Backends that do
not implement the audit profile advertise `governance.audit.supported:
false` and behave exactly as v1.3 specifies today. Backends that
implement it expose a uniform attestation surface that compliance tools,
GRC platforms, and external auditors can consume across vendors.

---

## 1. Motivation

OAMP backends already store the evidence auditors need: governance
classes per entry, label distributions, provenance, audit-log events,
grant lifecycle records, retention timestamps, and (under v1.3) grant
denials. Today there is no portable way to read that evidence.

In practice this means:

- **Custom auditor onboarding per vendor.** Every OAMP-compliant
  product reinvents an admin export, a CSV dump, or a "share my
  database" workflow for SOC 2, ISO 27001, HIPAA, or internal review.
  Auditors learn each vendor's schema separately. Compliance teams
  cannot compare two products against the same evidence model.
- **Over-privileged audit access.** Without a dedicated audit role,
  the common shortcut is to issue the auditor a full admin token or
  a database read replica. Both grant content access where only
  metadata is needed, and both bypass v1.3 enforcement entirely.
- **Self-attestation theatre.** Vendors publish trust pages and PDFs
  asserting governance posture. None of it is machine-verifiable
  against the running system. A regulator or customer cannot point
  a tool at the deployed backend and confirm the posture is what the
  PDF claims.
- **No standard for "auditor saw it."** Today, when an auditor reads
  user data, that read either is not logged, is logged the same way
  as agent reads (indistinguishable in retrospect), or is logged in
  a vendor-specific shape. There is no portable event class that
  says "compliance role accessed N entries under consent grant G."

This proposal closes those gaps by treating the auditor as a
first-class principal with its own scope vocabulary, its own endpoints,
and its own event classes, all reusing the v1.2/v1.3 governance
substrate rather than duplicating it.

## 2. Non-goals

- Defining a specific compliance framework. v1.4 exposes evidence; it
  does not assert that any given set of evidence proves SOC 2 CC6.1
  or HIPAA §164.312(b) compliance. Mapping is the auditor's job; §10
  is informative, not normative.
- Replacing existing GRC or SIEM tooling. v1.4 produces structured,
  signed JSON that those tools consume. It does not implement
  workflow, ticketing, or risk scoring.
- Standardising the audit-role issuance UI. Per v1.3 §5.2, issuance
  is the backend's responsibility under direct user / tenant-admin
  authentication. v1.4 specifies the claim shape and the endpoints,
  not the consent screen.
- Standardising auditor identity federation. Auditors may be
  identified by mTLS client certificates, OIDC, or backend-issued
  bearer tokens; v1.4 is neutral on the mechanism, as v1.0 is for
  agent tokens.
- Defining a content-redaction or DLP layer for audit content access.
  Where audit-role content reads are permitted, the entry is returned
  unredacted under v1.0/v1.2 semantics. Redaction for audit purposes
  is out of scope and would conflict with the v2.0 withheld-results
  envelope work.

## 3. Design overview

Four additions, all reusing v1.2 metadata and v1.3 enforcement:

1. **An audit role and `oamp_audit_scope` claim**, distinct from
   agent grants (v1.3 §5.1). The role is granted by a tenant
   administrator or by the user under direct authentication, never
   inherited from an agent token.
2. **A family of `/v1/audit/*` endpoints** that read evidence
   already required by v1.0–v1.3: inventory aggregates, governance
   posture, audit-log events, erasure metrics, and grant summaries.
   These endpoints reject any caller without an `audit` role.
3. **A signed-attestation envelope** (JWS, RFC 7515) the backend
   wraps around every audit response. The signing key is a dedicated
   audit-attestation key, separate from the v1.3 grant-signing key
   and from at-rest encryption keys.
4. **Audit-specific event classes** added to the v1.3 audit log so
   that auditor activity is itself auditable using the same
   substrate, preventing "the auditor's eyes" from being a privileged
   blind spot.

## 4. The audit role

### 4.1 `oamp_audit_scope` claim

An audit-role token carries an `oamp_audit_scope` claim, which is an
array of one or more of the following scope values:

| Scope | Reads | Notes |
|-------|-------|-------|
| `metadata` | `/v1/audit/inventory`, `/v1/audit/policy`, `/v1/audit/retention` | Aggregate counts and governance posture. No per-entry identifiers. No content. Default. |
| `events` | `/v1/audit/events` | The v1.0 §8.2.6 / v1.3 §9 audit log. Per-event metadata only; content fields are stripped per `docs/security-guide.md` §5. |
| `grants` | `/v1/audit/grants` | Active and revoked grants summary. Includes `oamp_agent_id`, `oamp_grant_id`, label set, sensitivity max, TTL. Never includes raw token material. |
| `inventory.entry` | `/v1/audit/inventory/entries` | Per-entry structural metadata: `id`, `governance`, `provenance`, `created_at`, `updated_at`, retention deadline. No `content`, no `tags`, no `metadata` body. |
| `erasure` | `/v1/audit/erasure` | DSR fulfilment metrics: time-to-erasure distribution, outstanding requests, denied requests with non-PII reason codes. |
| `content` | `/v1/audit/entries/{id}` | Entry content under explicit user consent. MUST be time-bounded; see §4.3. |

The default audit-role token issued without explicit scope selection
MUST carry `oamp_audit_scope: ["metadata"]`. Backends MUST reject
audit-role tokens carrying any scope outside this enum with
`400 Bad Request` and audit-log `audit_token_invalid`.

The `metadata` scope is a strict subset of `inventory.entry`, which is
a strict subset of `content`. Backends MAY enforce this lattice by
denying explicit combinations (e.g. `["content"]` without
`["inventory.entry"]`); they MUST NOT silently upgrade.

### 4.2 Identity claims

The audit-role token carries:

```json
{
  "sub": "auditor:acme-assurance:eng-04",
  "oamp_role": "audit",
  "oamp_audit_scope": ["metadata", "events"],
  "oamp_audit_engagement_id": "eng-2026-Q2-soc2",
  "oamp_audit_tenant_id": "tenant-7",
  "oamp_audit_consent_id": null,
  "exp": 1747339200,
  "nbf": 1747252800
}
```

| Claim | Semantics |
|-------|-----------|
| `oamp_role` | MUST be `"audit"`. Distinguishes audit tokens from agent tokens (v1.3) and admin tokens (`/v1/admin/*`, v1.0 openapi). |
| `oamp_audit_engagement_id` | Stable identifier for the audit engagement. Joins every event the auditor causes to a single engagement record. |
| `oamp_audit_tenant_id` | Tenant whose data the audit covers. MUST be present on multi-tenant backends. |
| `oamp_audit_consent_id` | If `oamp_audit_scope` includes `content`, MUST reference the consent record authorising content access. Otherwise `null`. |
| `exp` | RECOMMENDED `≤ 24 hours` for `metadata`/`events`/`grants` scopes, `≤ 1 hour` for `content` scope. |

Audit tokens MUST NOT carry any of the v1.3 agent claims
(`oamp_agent_id`, `oamp_grant_id`, `oamp_read_labels`, `oamp_write_labels`,
`oamp_sensitivity_max`, `oamp_export_full`). A token that carries both
agent and audit claims MUST be rejected with `400 Bad Request`.

### 4.3 Consent for content access

The `content` scope requires a separate consent record. The minimum
shape of the consent record is:

```json
{
  "consent_id": "cns-2026-05-19-001",
  "engagement_id": "eng-2026-Q2-soc2",
  "subject_user_ids": ["u-42", "u-43"],
  "purpose": "soc2-type2-evidence-sampling",
  "granted_by": "user|tenant-admin|dpo",
  "granted_at": "2026-05-19T10:00:00Z",
  "expires_at": "2026-05-19T11:00:00Z",
  "max_entries": 50
}
```

The backend MUST refuse content reads outside `[granted_at, expires_at]`,
MUST refuse reads of entries whose `user_id` is not in
`subject_user_ids`, and MUST reject the engagement once `max_entries`
has been served. Each content read MUST emit an
`audit_content_access` event (§7) including `consent_id` and the read
entry id.

`granted_by: "user"` is the only acceptable source for content scoped
to a single user. `granted_by: "tenant-admin"` is permitted for
multi-user engagements only if the tenant's lawful basis is
established outside the protocol (employment contract, DPIA, court
order). Backends SHOULD surface tenant-admin content consent
prominently in the user-facing log per `docs/security-guide.md` §4
right-to-erasure transparency.

## 5. Audit endpoints

All audit endpoints sit under `/v1/audit/` and require an
`oamp_role: "audit"` token. Calls without the role MUST return
`401 Unauthorized` if unauthenticated and `403 Forbidden` if
authenticated as a non-audit principal. Existence hiding under v1.3
§6.2 does not apply here because the audit surface is by definition
an admin-class surface.

### 5.1 `GET /v1/audit/inventory`

Returns aggregate inventory: counts grouped by `governance.sensitivity_class`
and by reserved top-level `governance.labels` (v1.3 §4.2). No
per-entry identifiers. Scope: `metadata`.

Response shape:

```json
{
  "tenant_id": "tenant-7",
  "as_of": "2026-05-19T14:00:00Z",
  "totals": {
    "entries": 18421,
    "users": 312,
    "by_sensitivity_class": {
      "public": 124, "internal": 14002,
      "confidential": 4011, "restricted": 284
    },
    "by_top_level_label": {
      "identity": 312, "location": 1102, "health": 84,
      "finance": 41, "relationships": 980, "work": 12011,
      "preferences": 2901, "creative": 1100, "beliefs": 12,
      "behaviour": 880
    },
    "by_handling_retrieval": { "governed": 18137, "ungoverned": 284 }
  }
}
```

### 5.2 `GET /v1/audit/policy`

Returns the backend's full governance and enforcement posture, drawn
from v1.1 capabilities, v1.2 governance capability, and v1.3
`governance.enforcement`. Adds operational data the capabilities
endpoint does not surface: at-rest encryption algorithm, key-rotation
age, audit-log retention window, deletion mode (zeroize/drop).
Scope: `metadata`.

```json
{
  "oamp_version": "1.4.0",
  "capabilities_ref": "/v1/capabilities",
  "encryption_at_rest": {
    "algorithm": "AES-256-GCM",
    "active_key_id": "k-2026-04",
    "active_key_age_days": 39,
    "rotation_policy_days": 90
  },
  "deletion_mode": "zeroize-and-drop",
  "audit_log": {
    "retention_days": 365,
    "tamper_evident": "hash-chain",
    "signed_export_supported": true
  },
  "enforcement": {
    "v1_3_supported": true,
    "existence_hiding": true,
    "stream_filtering": true
  },
  "regional_residency": ["eu-west-1", "us-east-1"]
}
```

### 5.3 `GET /v1/audit/events`

Returns paginated audit log entries (`docs/security-guide.md` §5)
extended with the v1.3 actions and the §7 audit-role actions.
Same filter parameters as `/v1/admin/audit`, plus `since`, `until`,
`engagement_id`. Scope: `events`.

Entries MUST NOT contain knowledge content, `tags`, or `metadata`
body. The `detail` field is per v1.0 §8.1.3 / v1.3 §9 (label set,
not entry id, for `scope_denied_read`).

### 5.4 `GET /v1/audit/erasure`

Returns metrics for the right-to-erasure requirement
(`docs/security-guide.md` §4, GDPR Art. 17, CCPA §1798.105).
Scope: `erasure`.

```json
{
  "as_of": "2026-05-19T14:00:00Z",
  "window_days": 90,
  "requests": {
    "received": 41, "fulfilled": 39, "pending": 2, "denied": 0
  },
  "time_to_fulfilment_seconds": {
    "p50": 32, "p95": 184, "max": 2102
  },
  "outstanding_oldest_seconds": 3604,
  "deletion_mode": "zeroize-and-drop"
}
```

### 5.5 `GET /v1/audit/grants`

Returns active and recently-revoked v1.3 grants. Scope: `grants`.
The response MUST NOT contain raw JWT material, signing keys, or
refresh tokens.

```json
{
  "as_of": "2026-05-19T14:00:00Z",
  "active": [
    {
      "grant_id": "grant-2026-05-07-001",
      "agent_id": "medical-assistant-v3",
      "user_id": "u-42",
      "read_labels": ["health", "preferences"],
      "write_labels": ["health", "preferences"],
      "sensitivity_max": "restricted",
      "issued_at": "2026-05-07T09:00:00Z",
      "expires_at": "2026-05-08T09:00:00Z"
    }
  ],
  "revoked_window_days": 30,
  "revoked_count": 4
}
```

### 5.6 `GET /v1/audit/inventory/entries`

Per-entry structural metadata, paginated. Scope: `inventory.entry`.
Each entry includes `id`, `user_id`, `governance`, `provenance`,
`created_at`, `updated_at`, `retention.expires_at` if applicable.
MUST omit `content`, `tags`, `metadata`, and any free-text body
fields. This is the "what shape is the data, without seeing it"
view that most external assessors actually want.

### 5.7 `GET /v1/audit/entries/{id}`

Returns full entry including content. Scope: `content`. Requires
`oamp_audit_consent_id` on the token. Backends MUST verify the
entry's `user_id` is in the consent record's `subject_user_ids`,
the current time is within the consent window, and `max_entries`
has not been exhausted. Each call emits `audit_content_access`
(§7).

### 5.8 `POST /v1/audit/attest`

Requests a signed, point-in-time attestation report bundling
inventory, policy, erasure, and a hash of the events page over the
given window. Scope: union of `metadata` and `events`. Returns the
v1.4 attestation envelope (§6) directly.

Request:

```json
{
  "report_type": "soc2-evidence-snapshot",
  "window": { "since": "2026-04-01T00:00:00Z",
              "until": "2026-04-30T23:59:59Z" },
  "include": ["inventory", "policy", "erasure", "events_hash"]
}
```

`report_type` is a free-form string; the §10 mapping defines
suggested values for common standards. The backend MUST NOT
interpret it as a policy claim; it is metadata for the consuming
GRC tool.

## 6. Signed attestation envelope

Every response from a `/v1/audit/*` endpoint MUST be wrapped in a
JWS (RFC 7515) compact serialisation when the request carries an
`Accept: application/jose+json` header, and MAY be wrapped by
default. The unwrapped JSON form (`Accept: application/json`)
remains available for interactive use but SHOULD NOT be used as
archival evidence.

Envelope payload:

```json
{
  "iss": "https://memory.example.com",
  "sub": "tenant-7",
  "iat": 1747252800,
  "aud_engagement": "eng-2026-Q2-soc2",
  "oamp_audit_endpoint": "/v1/audit/inventory",
  "oamp_audit_scope": ["metadata"],
  "oamp_version": "1.4.0",
  "payload_sha256": "b3a1...c7",
  "payload": { /* the endpoint's response body */ }
}
```

The JWS header MUST set `alg` to `EdDSA` (Ed25519, RECOMMENDED) or
`ES256`. `kid` MUST identify a key advertised at
`GET /.well-known/oamp-audit-jwks`. The key MUST be distinct from:

- The v1.0 at-rest encryption key (`docs/security-guide.md` §2)
- The v1.3 grant-signing key (`spec/proposals/2026-05-07-permissioned-memory-v1.3.md` §5.2)
- TLS server certificates

Key rotation SHOULD follow the same cadence as the encryption-key
rotation policy (`docs/security-guide.md` §3). Revoked `kid` values
MUST remain resolvable in JWKS so historical attestations remain
verifiable; resolve, do not delete.

`payload_sha256` is the SHA-256 of the canonical-JSON serialisation
of `payload` (RFC 8785 JCS). A verifier that does not understand
JCS can still verify the JWS signature; JCS is provided for
verifiers that wish to confirm the hash without re-serialising.

## 7. Audit-role event classes

Extend the audit-log `action` enum (v1.3 §9) with:

| Action | Triggered by | `detail` field |
|--------|--------------|----------------|
| `audit_session_open` | Audit token first used in a clock minute | `engagement_id`, `audit_scope`, `auditor_sub` |
| `audit_session_close` | TTL expiry or explicit logout | `engagement_id`, `audit_scope`, `auditor_sub` |
| `audit_metadata_read` | `/v1/audit/inventory`, `/policy`, `/retention`, `/grants` | `engagement_id`, endpoint |
| `audit_events_read` | `/v1/audit/events` | `engagement_id`, window, page size |
| `audit_inventory_entry_read` | `/v1/audit/inventory/entries` | `engagement_id`, page size; no entry ids |
| `audit_content_access` | `/v1/audit/entries/{id}` | `engagement_id`, `consent_id`, `entry_id`, `user_id` |
| `audit_attestation_emit` | `POST /v1/audit/attest` | `engagement_id`, `report_type`, `kid`, `payload_sha256` |
| `audit_token_invalid` | Malformed audit scope or claim mismatch | `auditor_sub`, reason code |

`audit_content_access` is the one action that intentionally includes
`entry_id` and `user_id`, because the consent record makes those
non-secret to the audit log and the regulator's expectation is that
content reads are individually traceable. This is the explicit
exception to the v1.0 §8.1.3 "no entry id correlation" guidance for
filtered events.

## 8. Capabilities advertisement

Extend the v1.2 `capabilities.governance` block with an `audit`
sub-block:

```json
{
  "oamp_version": "1.4.0",
  "capabilities": {
    "governance": {
      "supported": true,
      "enforcement": { "supported": true, "spec_version": "1.3.0" },
      "audit": {
        "supported": true,
        "spec_version": "1.4.0",
        "scopes": [
          "metadata", "events", "grants",
          "inventory.entry", "erasure", "content"
        ],
        "signed_attestation": {
          "supported": true,
          "algorithms": ["EdDSA", "ES256"],
          "jwks_uri": "/.well-known/oamp-audit-jwks"
        },
        "report_types": [
          "soc2-evidence-snapshot",
          "iso27001-evidence-snapshot",
          "iso27701-evidence-snapshot",
          "iso42001-evidence-snapshot",
          "hipaa-security-rule-evidence",
          "gdpr-art30-record",
          "ccpa-cybersecurity-audit",
          "eu-ai-act-art12-record",
          "nist-800-53-au-family",
          "pci-dss-10-evidence"
        ],
        "content_access": {
          "supported": true,
          "requires_consent_record": true,
          "max_consent_window_seconds": 3600
        }
      }
    }
  }
}
```

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `audit.supported` | boolean | MUST if `audit` present | Backend implements §5 endpoints |
| `audit.spec_version` | string | MUST | Version of this proposal implemented |
| `audit.scopes` | array of string | MUST | Subset of §4.1 scopes the backend supports |
| `audit.signed_attestation.supported` | boolean | MUST | Backend wraps responses in §6 envelope |
| `audit.signed_attestation.algorithms` | array of string | MUST | JWS `alg` values supported. MUST include at least one of `EdDSA`, `ES256` |
| `audit.signed_attestation.jwks_uri` | string | MUST | Resolves to a JWKS document for verification |
| `audit.report_types` | array of string | MUST | `report_type` values §5.8 accepts |
| `audit.content_access` | object | MUST if `content` in `scopes` | Consent requirements and limits |

## 9. Worked example (non-normative)

An external SOC 2 Type II assessor `acme-assurance` is engaged for
tenant `tenant-7`. The tenant administrator issues an audit token:

```json
{
  "sub": "auditor:acme-assurance:eng-04",
  "oamp_role": "audit",
  "oamp_audit_scope": ["metadata", "events", "grants"],
  "oamp_audit_engagement_id": "eng-2026-Q2-soc2",
  "oamp_audit_tenant_id": "tenant-7",
  "exp": 1747339200
}
```

The auditor's GRC tool calls:

```http
POST /v1/audit/attest
Accept: application/jose+json
Authorization: Bearer eyJ...

{ "report_type": "soc2-evidence-snapshot",
  "window": { "since": "2026-04-01T00:00:00Z",
              "until": "2026-04-30T23:59:59Z" },
  "include": ["inventory", "policy", "erasure", "events_hash"] }
```

The backend returns a single compact JWS. The GRC tool verifies the
signature against `/.well-known/oamp-audit-jwks`, stores the JWS as
evidence artefact `EV-2026-04-acme-soc2-01`, and indexes the
payload's claims against the assessor's CC6.1 / CC7.2 / C1.1
worksheet (see §10.1).

For the entire engagement, no entry content has been read. The
auditor produced their report from aggregate counts, policy
posture, erasure metrics, grant lifecycle, and the signed audit-log
events page. If sampling is required, the tenant DPO issues a
content-consent record for the specific user ids under audit, the
auditor obtains a separate short-lived `content`-scoped token, and
each read of `/v1/audit/entries/{id}` is itself audit-logged and
returned in a signed envelope.

## 10. Mapping to real-world standards (informative)

This section is non-normative. It exists so backend authors,
auditors, and procurement teams can see which v1.4 surface maps to
which clause of the standards they actually have to comply with.
Mappings are not exhaustive; they identify the v1.4 surface that
most directly satisfies each clause.

### 10.1 SOC 2 (AICPA TSC 2017, 2022 points-of-focus)

| Trust Services Criterion | v1.4 surface |
|--------------------------|--------------|
| CC6.1 logical access controls | `/v1/audit/grants`, `/v1/audit/policy.enforcement` |
| CC6.2 provisioning and de-provisioning | `audit_log.action ∈ {grant_issue, grant_revoke}` via `/v1/audit/events` |
| CC6.3 authorisation of access changes | `/v1/audit/grants.revoked_count`, `grant_revoke` events |
| CC7.2 system monitoring (anomaly detection) | `scope_denied_read`, `scope_denied_write` events |
| CC7.3 evaluation of security events | Signed §6 envelope with event-window hash |
| C1.1 confidentiality protection | `/v1/audit/policy.encryption_at_rest`, `governance.sensitivity_class` distribution |
| C1.2 disposal of confidential information | `/v1/audit/erasure`, `/v1/audit/policy.deletion_mode` |
| P1.1 notice of privacy practices | Out of scope for v1.4; covered by product UX |
| P4.2 access management | `/v1/audit/grants` |
| P5.1 access requests (data subject) | `/v1/audit/erasure` (right-to-know not modelled separately) |
| P5.2 deletion requests | `/v1/audit/erasure` |

Suggested `report_type`: `soc2-evidence-snapshot`.

### 10.2 ISO/IEC 27001:2022 (Annex A controls)

| Control | v1.4 surface |
|---------|--------------|
| A.5.10 acceptable use of information | `/v1/audit/policy`, `governance.handling` distribution |
| A.5.15 access control | `/v1/audit/grants` |
| A.5.31 legal, statutory, regulatory and contractual requirements | `/v1/audit/policy.regional_residency`, `report_type: gdpr-art30-record` |
| A.8.2 privileged access rights | `/v1/audit/grants` filtered by `sensitivity_max ∈ {confidential, restricted}` |
| A.8.10 information deletion | `/v1/audit/erasure`, `/v1/audit/policy.deletion_mode` |
| A.8.12 data leakage prevention | `scope_denied_read` rate via `/v1/audit/events` |
| A.8.15 logging | `/v1/audit/events`, §6 signed envelope |
| A.8.16 monitoring activities | `/v1/audit/events` filtered by `audit_*` actions |
| A.8.24 use of cryptography | `/v1/audit/policy.encryption_at_rest`, JWKS for §6 |
| A.8.34 protection of information systems during audit testing | §7 audit-role event classes (auditor activity is itself logged) |

Suggested `report_type`: `iso27001-evidence-snapshot`.

### 10.3 ISO/IEC 27701:2019 (Privacy Information Management)

Extension of 27001 for PII processors and controllers.

| Clause | v1.4 surface |
|--------|--------------|
| 6.3 records of processing activities | `report_type: gdpr-art30-record` payload from `/v1/audit/inventory` + `/v1/audit/policy.regional_residency` |
| 7.2.6 obligations to PII principals | `/v1/audit/erasure`, `audit_content_access` consent records |
| 7.4.5 PII minimisation | `governance.labels` distribution, `inventory.by_top_level_label` |
| 8.5.4 transfer or disclosure | `audit_log.action = export` events, `audit_content_access` events |

Suggested `report_type`: `iso27701-evidence-snapshot`.

### 10.4 ISO/IEC 42001:2023 (AI Management System)

The newest of these, AI-specific, and the one OAMP is most natively
shaped for.

| Clause | v1.4 surface |
|--------|--------------|
| 6.1.4 AI risk assessment | `/v1/audit/policy.enforcement`, `inventory.by_sensitivity_class` |
| 8.3 AI data quality and provenance | `provenance` on every entry via `/v1/audit/inventory/entries`; v1.2 multi-source `provenance.sources` |
| 8.4 AI system impact on individuals | `audit_content_access` traceability, `scope_denied_read` distribution |
| A.4 data resource governance | Full `/v1/audit/policy` |
| A.6 AI system documentation | `report_type: iso42001-evidence-snapshot` |

Suggested `report_type`: `iso42001-evidence-snapshot`.

### 10.5 HIPAA Security Rule (45 CFR §164.308–316)

| Section | v1.4 surface |
|---------|--------------|
| §164.308(a)(1)(ii)(D) information system activity review | `/v1/audit/events` |
| §164.308(a)(3) workforce access management | `/v1/audit/grants` filtered by `sensitivity_max = restricted` and `read_labels ∋ health` |
| §164.308(a)(4) information access management | `grant_issue` / `grant_revoke` events |
| §164.312(a)(1) access control | v1.3 enforcement; surfaced via `/v1/audit/policy.enforcement` |
| §164.312(b) audit controls | `/v1/audit/events` + §6 signed envelope (tamper-evidence) |
| §164.312(c)(1) integrity | `audit_log.tamper_evident` field in `/v1/audit/policy` |
| §164.524 patient right of access | DSR fulfilment not directly modelled; partially via `/v1/audit/erasure` adjacency |
| §164.530(j) documentation retention (6 years) | `/v1/audit/policy.audit_log.retention_days ≥ 2190` |

Suggested `report_type`: `hipaa-security-rule-evidence`. Note that
HIPAA requires a BAA between the covered entity and the OAMP
backend operator; v1.4 does not standardise BAA exchange.

### 10.6 GDPR (Regulation (EU) 2016/679)

| Article | v1.4 surface |
|---------|--------------|
| Art. 5(1)(c) data minimisation | `inventory.by_top_level_label`, `inventory.by_sensitivity_class` |
| Art. 5(1)(e) storage limitation | `/v1/audit/policy.audit_log.retention_days`, retention deadlines via `/v1/audit/inventory/entries` |
| Art. 5(1)(f) integrity and confidentiality | `/v1/audit/policy.encryption_at_rest` |
| Art. 15 right of access | `/v1/audit/erasure` adjacency; the v1.0 `/v1/export` is the data-subject-facing surface |
| Art. 17 right to erasure | `/v1/audit/erasure` |
| Art. 25 data protection by design | `/v1/audit/policy.enforcement`, v1.3 grants |
| Art. 30 records of processing activities | `report_type: gdpr-art30-record` |
| Art. 32 security of processing | Full `/v1/audit/policy` |
| Art. 33 breach notification (72h) | `/v1/audit/events` enables breach scope determination; v1.4 does not implement notification |
| Art. 35 DPIA | `/v1/audit/inventory.by_sensitivity_class`, `governance.sensitivity_class = restricted` count |
| Art. 88 (employment context) | Combined with §10.10 workforce mapping |

Suggested `report_type`: `gdpr-art30-record`.

### 10.7 CCPA / CPRA (Cal. Civ. Code §1798)

| Section | v1.4 surface |
|---------|--------------|
| §1798.100 right to know | `/v1/audit/inventory/entries` (auditor side); `/v1/export` (consumer side) |
| §1798.105 right to delete | `/v1/audit/erasure` |
| §1798.106 right to correct | Not modelled in v1.4; v1.0 update path |
| §1798.121 right to limit use of sensitive PI | `governance.sensitivity_class = confidential|restricted` + `governance.handling.retrieval = governed` |
| §1798.130 notice at collection | Out of scope |
| §1798.185(a)(15) annual cybersecurity audit (CPRA) | `report_type: ccpa-cybersecurity-audit` |

Suggested `report_type`: `ccpa-cybersecurity-audit`.

### 10.8 EU AI Act (Regulation (EU) 2024/1689, in force from 2026)

For deployers of general-purpose and high-risk AI systems, the
audit profile maps as follows:

| Article | v1.4 surface |
|---------|--------------|
| Art. 10 data and data governance | `/v1/audit/inventory`, `governance.labels` distribution, `provenance` |
| Art. 12 record-keeping (high-risk AI) | `/v1/audit/events`, §6 signed envelope, `report_type: eu-ai-act-art12-record` |
| Art. 13 transparency to deployers | `/v1/audit/policy`, `capabilities` discovery |
| Art. 14 human oversight | `/v1/audit/grants` (per-agent oversight surface) |
| Art. 15 accuracy, robustness, cybersecurity | `/v1/audit/policy.encryption_at_rest`, `scope_denied_*` rates |
| Art. 26(6) deployer logs retention (≥ 6 months) | `/v1/audit/policy.audit_log.retention_days ≥ 180` |
| Art. 27 fundamental rights impact assessment | `inventory.by_sensitivity_class`, `by_top_level_label ∋ {health, beliefs, identity}` |

Suggested `report_type`: `eu-ai-act-art12-record`.

### 10.9 NIST frameworks

**NIST SP 800-53 Rev 5** (AU family — Audit and Accountability):

| Control | v1.4 surface |
|---------|--------------|
| AU-2 event logging | `/v1/audit/events` |
| AU-3 content of audit records | Event schema (v1.3 §9 + §7) |
| AU-6 audit record review, analysis, reporting | `/v1/audit/events` + GRC tool consumption |
| AU-9 protection of audit information | §6 signed envelope; separate signing key |
| AU-11 audit record retention | `/v1/audit/policy.audit_log.retention_days` |
| AU-12 audit record generation | All v1.4 endpoints emit §7 events |

Suggested `report_type`: `nist-800-53-au-family`.

**NIST AI Risk Management Framework (AI RMF 1.0)** functions —
Govern, Map, Measure, Manage — map most directly to:

| Function | v1.4 surface |
|----------|--------------|
| GOVERN | `/v1/audit/policy`, `/v1/audit/grants` |
| MAP | `/v1/audit/inventory`, `governance.labels` |
| MEASURE | `/v1/audit/events`, `scope_denied_*` rates, `audit_content_access` rate |
| MANAGE | `/v1/audit/erasure`, `grant_revoke` events |

**NIST Cybersecurity Framework 2.0** functions — Identify, Protect,
Detect, Respond, Recover, Govern — map to the same v1.4 surfaces
with `/v1/audit/policy` carrying the bulk of Identify and Govern,
`/v1/audit/events` carrying Detect, and `/v1/audit/erasure` plus
`grant_revoke` carrying Respond.

### 10.10 Sector-specific frameworks

| Framework | Sector | v1.4 surface |
|-----------|--------|--------------|
| PCI DSS 4.0 §10 | Card payments | `/v1/audit/events` (10.2), §6 envelope (10.3), retention ≥ 365 days (10.5) |
| FINRA Rule 4511, SEC 17a-4(f) | US broker-dealers | `/v1/audit/policy.audit_log` write-once enforcement; suggested `report_type: finra-4511-evidence` (vendor-specific) |
| FCA SYSC 9, MiFID II Art. 16 | UK/EU financial conduct | `/v1/audit/policy.audit_log.retention_days ≥ 1825` (5 years) |
| GLBA Safeguards Rule (16 CFR 314) | US financial institutions | `/v1/audit/policy.encryption_at_rest`, `/v1/audit/events` |
| FERPA (20 USC 1232g) | US education | `/v1/audit/grants` per-agent compartmentalisation maps to "school official" doctrine |
| COPPA (16 CFR 312) | US children's services | `/v1/audit/erasure`, `governance.labels ∋ identity` with `sensitivity_class = restricted` |
| HITRUST CSF v11 | Healthcare aggregator | Composed of HIPAA, ISO 27001, NIST mappings above |
| FedRAMP (Moderate / High) | US federal cloud | Composed of NIST 800-53 mapping above; `/v1/audit/policy.regional_residency` for boundary attestation |
| ITAR / EAR | US export control | `/v1/audit/policy.regional_residency`, `governance.sensitivity_class = restricted` |
| Cyber Essentials, Cyber Essentials Plus (UK) | UK SME baseline | `/v1/audit/policy.encryption_at_rest`, `/v1/audit/policy.enforcement` |
| Essential Eight (Australia ACSC) | AU baseline | `/v1/audit/grants` (privileged access), `/v1/audit/events` |
| K-ISMS / ISMS-P (South Korea) | KR | Composed of ISO 27001/27701 mappings above |
| APPI (Japan) | JP personal information | `/v1/audit/erasure`, `governance.labels` |

## 11. Industry applicability (informative)

Concrete product categories that can adopt the audit profile, with
the dominant standards each cares about and the v1.4 scope mix they
typically need:

| Product / industry | Dominant standards | Typical scopes |
|--------------------|--------------------|----------------|
| Consumer AI assistants storing personal memory | GDPR, CCPA/CPRA | `metadata`, `erasure` |
| Workplace AI assistants (HR-adjacent) | GDPR Art. 88, ISO 27701, SOC 2 | `metadata`, `events`, `grants` |
| Medical / clinical AI copilots | HIPAA, HITRUST, GDPR-health, ISO 42001 | `metadata`, `events`, `grants`, `content` (with consent) |
| Mental-health and therapy chat products | HIPAA (US), MHRA / NHS DTAC (UK), GDPR-health | `metadata`, `events`, `erasure`, `content` (with consent) |
| Financial advisor / wealth AI | GLBA, FINRA 4511, SEC 17a-4, FCA SYSC, MiFID II | `metadata`, `events`, `grants` (with extended retention) |
| Payments and PoS agents | PCI DSS 4.0 | `metadata`, `events` |
| Enterprise productivity / code assistants | SOC 2 Type II, ISO 27001, EU AI Act Art. 26 | `metadata`, `events`, `grants` |
| Education and tutoring AI for minors | FERPA, COPPA, GDPR-K | `metadata`, `erasure`, `inventory.entry` |
| Government / public-sector AI deployers | FedRAMP, NIST 800-53, EU AI Act high-risk | All scopes; `signed_attestation` mandatory |
| Defense / classified-adjacent | ITAR/EAR, NIST 800-171, IL-grade clouds | `metadata`, `events`, `grants`; air-gapped JWKS |
| Legal AI (privilege-bearing memory) | ABA Model Rule 1.6, SRA Standards | `metadata`, `events`, `content` (privileged-consent records) |
| Insurance underwriting AI | GDPR Art. 22, NAIC AI Model Bulletin, EU AI Act high-risk | `metadata`, `inventory.entry`, `events` |
| Adtech / marketing personalisation | GDPR, CPRA, IAB TCF | `metadata`, `erasure` |
| Children-facing AI (toys, edtech) | COPPA, EU AI Act, Age-Appropriate Design Code | `metadata`, `erasure`, `inventory.entry` |
| Critical infrastructure AI deployers | NIS2 (EU), CIRCIA (US) | `metadata`, `events`, signed `attest` |

A general rule: the more sensitive the sector, the more of the
`scopes` list its auditors will exercise, and the more important
the §6 signed envelope becomes as an archival artefact.

## 12. Threat model deltas

What this proposal closes:

- **Audit-channel over-privilege.** Auditors no longer need admin
  tokens. The `metadata` scope is the default, and it carries no
  per-entry identifiers and no content.
- **Self-attestation theatre.** Policy claims (encryption algorithm,
  rotation cadence, deletion mode, enforcement posture) are exposed
  on a uniform endpoint and signed under a dedicated key. A
  customer's risk team can verify them without trusting a PDF.
- **Hidden auditor activity.** Every audit-role read is logged via §7
  with `engagement_id`. The auditor cannot read user data without
  leaving the same kind of trail an agent leaves.
- **Vendor-lock-in for compliance evidence.** A GRC tool consuming
  signed §6 envelopes from one OAMP backend understands the
  envelopes from any other OAMP backend implementing v1.4.

What it does not close:

- **Compromised audit-signing key.** If a backend's audit-signing
  key leaks, all attestations from that backend become forgeable.
  Treat the key with the same handling as the at-rest encryption
  key.
- **Colluding auditor.** A scoped auditor that legitimately reads
  metadata and then exfiltrates it outside the protocol. v1.4
  shrinks the leak (no content by default) but cannot remove trust
  in the auditor entity.
- **Inference from aggregates.** A `/v1/audit/inventory` response
  with `by_top_level_label.health = 1` on a single-user tenant
  reveals that the user has at least one health entry. Backends
  SHOULD apply k-anonymity (RECOMMENDED `k ≥ 5`) to inventory
  buckets on small tenants, or report counts as ranges.
- **Standards drift.** §10 is informative and current as of the
  publication date. Standards evolve; new ones appear. Updating
  this section is not a normative change to the protocol.

## 13. Backwards compatibility

- v1.4 is purely additive. v1.0–v1.3 entries, tokens, and clients
  function unchanged on a v1.4 backend.
- The existing `/v1/admin/audit` endpoint (v1.0 openapi line 722)
  remains available. v1.4 RECOMMENDS deprecating it in favour of
  `/v1/audit/events` over a 12-month window once v1.4 is final.
  Until then, backends MAY serve both, with `/v1/audit/events`
  enforcing audit-role scope and `/v1/admin/audit` continuing to
  require admin role.
- Backends that do not implement v1.4 MUST advertise
  `governance.audit.supported: false` (or omit the `audit`
  sub-block entirely). Compliance tools MUST inspect capabilities
  before requesting `/v1/audit/*` endpoints.
- Audit tokens issued against a v1.4 backend MUST NOT be accepted
  by v1.0–v1.3 endpoints; the `oamp_role: "audit"` claim signals
  that the principal is not an agent and has no agent grant.

## 14. Conformance summary

A v1.4-conformant backend that advertises
`governance.audit.supported: true` MUST:

- Continue to satisfy every v1.0, v1.1, v1.2, and (if advertising
  `enforcement.supported: true`) v1.3 requirement.
- Implement at least the `metadata` and `events` scopes per §4.1.
- Reject audit tokens with mixed agent/audit claims per §4.2.
- Enforce consent-record bounds for any `content` scope per §4.3.
- Implement the §5 endpoints corresponding to its advertised
  scopes, and reject calls outside those scopes with `403 Forbidden`.
- Sign responses per §6 when `Accept: application/jose+json` is
  requested, using a key advertised at the JWKS URI.
- Maintain the audit-signing key as a separate cryptographic
  resource from the at-rest encryption key, the v1.3 grant-signing
  key, and TLS certificates.
- Emit the §7 events for every audit-role read.
- Advertise the `governance.audit` block per §8.

A v1.4-conformant backend that does not implement audit MUST:

- Continue to satisfy every v1.0–v1.3 requirement.
- Advertise `governance.audit.supported: false` or omit the block.
- NOT accept `oamp_role: "audit"` tokens on any endpoint.

## 15. Open questions

- **Federated audit identity.** Should auditors be identified via
  OIDC federation, mTLS client certificates, or backend-issued
  bearer tokens? The current draft is neutral, but a portable
  federation profile (e.g. an "audit OIDC" claim binding) would
  let one auditor onboard once across many OAMP backends. Likely
  a v1.5 follow-up.
- **k-anonymity floor for `/v1/audit/inventory`.** Should the
  protocol mandate `k ≥ 5` bucketing on small tenants, or leave
  it to deployment policy? The trade-off is between protecting
  small-tenant users from aggregate inference and giving auditors
  precise counts.
- **Tamper-evident chain format.** `/v1/audit/policy.audit_log.tamper_evident`
  is a free-form string today. A normative format (hash-chain
  with periodic `kid`-signed checkpoints, or a transparency-log
  style Merkle tree) would let auditors verify completeness
  without trusting the backend's claim. Likely a v1.5 item.
- **Cross-backend report consolidation.** A consumer running OAMP
  memory across two backends (e.g. one for medical agent, one
  for general agent — exactly the v1.3 motivating scenario)
  needs a way to consolidate audit evidence. v1.4 does not
  define a federation envelope; each backend signs its own. A
  client-side aggregator is the path of least resistance.
- **Right-to-know vs. right-to-erasure.** v1.4 surfaces erasure
  but not access-request fulfilment metrics. GDPR Art. 15 and
  CCPA §1798.110 both have right-to-know clocks. A
  `/v1/audit/access-requests` endpoint analogous to
  `/v1/audit/erasure` is a small additive extension worth
  prototyping.
- **DPA / BAA exchange.** HIPAA requires a Business Associate
  Agreement; GDPR requires a Data Processing Agreement. v1.4
  does not standardise their exchange. A
  `/v1/audit/policy.contracts` block listing executed agreement
  hashes is a candidate v1.5 addition.

## 16. Implementation checklist

For backends adopting this proposal:

- [ ] Mint an audit-attestation key pair distinct from existing keys
- [ ] Publish the audit JWKS at `/.well-known/oamp-audit-jwks`
- [ ] Implement audit-role token validation (`oamp_role`, scope
      enum, no agent claims, no admin claims)
- [ ] Implement consent record storage and the §4.3 enforcement
- [ ] Implement §5.1 `/v1/audit/inventory`
- [ ] Implement §5.2 `/v1/audit/policy` drawing from existing
      capability and config sources
- [ ] Implement §5.3 `/v1/audit/events` (may reuse `/v1/admin/audit`
      backing store)
- [ ] Implement §5.4 `/v1/audit/erasure` from existing right-to-erasure
      bookkeeping
- [ ] Implement §5.5 `/v1/audit/grants` from the v1.3 grant store
- [ ] Implement §5.6 `/v1/audit/inventory/entries` with content
      strictly omitted
- [ ] Implement §5.7 `/v1/audit/entries/{id}` with consent-bounded
      content access
- [ ] Implement §5.8 `POST /v1/audit/attest` returning §6 JWS
- [ ] Wrap responses in §6 JWS when `Accept: application/jose+json`
- [ ] Emit §7 events for every audit-role read
- [ ] Advertise `governance.audit` block per §8
- [ ] Add cross-implementation conformance fixtures under
      `validators/test-fixtures/` covering scope enforcement, JWS
      verification, consent-window expiry, content-quota exhaustion,
      and mixed agent/audit claim rejection

## References

- OAMP v1.0 Spec §8 (Privacy and Security Requirements), §10.3 (Field Evolution)
- OAMP v1.1 Draft §2 (Capabilities Discovery)
- OAMP v1.2 Draft §3 (`KnowledgeEntry` Additions: governance, provenance), §4 (Capabilities Additions)
- OAMP v1.3 Proposal (Permissioned Memory, enforcement layer)
- `docs/security-guide.md` §1 (Threat Model), §2 (Encryption at Rest), §4 (Right to Erasure), §5 (No Content in Logs), §8 (Audit Logging)
- RFC 7515 (JSON Web Signature)
- RFC 7517 (JSON Web Key)
- RFC 7519 (JSON Web Tokens)
- RFC 8785 (JSON Canonicalization Scheme)
- AICPA Trust Services Criteria (SOC 2)
- ISO/IEC 27001:2022; ISO/IEC 27701:2019; ISO/IEC 42001:2023
- HIPAA Security Rule, 45 CFR §§ 164.308–164.316
- Regulation (EU) 2016/679 (GDPR)
- Regulation (EU) 2024/1689 (EU AI Act)
- Cal. Civ. Code §1798.100 et seq. (CCPA / CPRA)
- NIST SP 800-53 Rev 5 (Audit and Accountability family)
- NIST AI Risk Management Framework 1.0
- NIST Cybersecurity Framework 2.0
- PCI DSS 4.0
- FINRA Rule 4511; SEC Rule 17a-4
- FCA SYSC 9; MiFID II Art. 16
- GLBA Safeguards Rule, 16 CFR 314
- FERPA, 20 USC 1232g; COPPA, 16 CFR 312
