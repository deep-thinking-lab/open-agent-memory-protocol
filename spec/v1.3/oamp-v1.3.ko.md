# 오픈 에이전트 메모리 프로토콜 — 버전 1.3.0 (초안)

**상태:** 초안 (제안된 마이너 버전)  
**날짜:** 2026-05-07  
**저자:** Jonathan Conway (Deep Thinking)  
**대체:** 없음 — v1.0.0, v1.1.0 및 v1.2.0을 추가적으로 확장  
**저장소:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 초록

OAMP v1.3은 v1.0.0 및 선택적 v1.1과 v1.2 초안 기능에 대한 **엄격히 추가적인** 마이너 버전입니다. 이는 v1.2에서 설명적으로 도입된 관리 메모리에 대한 **강제** 계층을 표준화합니다.

v1.2는 다음을 표준화했습니다:

- `governance.sensitivity_class`
- `governance.labels`
- `governance.handling`
- 더 풍부한 `provenance`
- 거버넌스 기능 발견

v1.3은 동일한 사용자의 여러 에이전트가 동일한 백엔드에 접근할 때 백엔드가 이러한 필드로 무엇을 해야 하는지를 정의합니다. 이는 다음을 표준화합니다:

- 휴대 가능한 에이전트 권한 주장
- 계층적 레이블 일치 규칙
- 읽기, 쓰기, 가져오기, 내보내기 및 스트림 필터링 규칙
- 에이전트 표면에서의 존재 숨기기
- provenance에 대한 에이전트 신원 바인딩
- 감사 로그 추가
- 강제 지원을 위한 기능 광고

v1.3은 **생략 기반**으로 남아 있습니다. 이는 휴대 가능한 withheld 또는 redacted 결과 문서를 표준화하지 않습니다. 해당 작업은 별도의 v2.0 트랙으로 연기됩니다.

이 문서의 "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", 및 "OPTIONAL"과 같은 키워드는 [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt)에서 설명된 대로 해석되어야 합니다.

---

## 1. 이전 버전과의 관계

v1.3은 모든 v1.0 스키마, 엔드포인트, 요구 사항 및 의미 규칙, 선택적 v1.1 기능 모델 및 추가적인 v1.2 관리 메모리 메타데이터 모델을 재사용합니다.

v1.3의 유일한 새로운 전송 수준 추가 사항은 다음과 같습니다:

- `GET /v1/capabilities`에서 OPTIONAL `capabilities.governance.enforcement`
- JWT 주장 또는 `OAMP-Grant`에 대한 휴대 가능한 에이전트 권한 주장 형식
- 기존 v1.2 `governance` 필드를 소비하는 규범적 백엔드 동작

v1.3은 **새로운 `KnowledgeEntry` 필드**와 **새로운 `KnowledgeStore` 필드**를 도입하지 않습니다.

v1.0-v1.2 항목/저장소 필드만 사용하는 문서는 `oamp_version`에 대해 `"1.2.0"`을 계속 사용할 수 있습니다. v1.3 초안 라인을 광고하고자 하는 문서 및 응답은 `"1.3.0"`을 사용할 수 있습니다.

---

## 2. 범위 분할

### 2.1 v1.3에서 표준화된 사항

- 휴대 가능한 에이전트별 권한 주장
- 계층적 거버넌스 레이블 강제 의미론
- v1.2 거버넌스 처리 힌트에 대한 운영적 의미
- 읽기 필터링
- 쓰기 거부
- 가져오기 거부 회계
- 내보내기 필터링 및 `oamp_export_full`
- v1.1 표면에서의 스트림 필터링
- 에이전트 표면에서의 존재 숨기기
- `oamp_agent_id`에 대한 provenance 바인딩
- 거버넌스 강제 기능 광고
- 권한 및 범위 이벤트에 대한 감사 작업 이름

### 2.2 v2.0으로 명시적으로 연기된 사항

- 표준화된 withheld 또는 redacted 결과 문서
- 가시 항목과 withheld 스텁을 포함하는 혼합 결과 세트
- 휴대 가능한 `withholding_reason` 의미론
- withheld 지식을 명시적으로 나타내는 스트림 페이로드
- 휴대 가능한 크로스 백엔드 권한 정책 언어

구현은 v1.3이 withheld 또는 redacted 스텁 문서를 표준화한다고 주장해서는 안 됩니다.

---

## 3. v1.2 거버넌스 메타데이터의 운영적 재사용

v1.3은 **새로운 항목 수준 거버넌스 필드**를 추가하지 않습니다. 대신 v1.2 필드를 운영적으로 만듭니다.

### 3.1 `governance.sensitivity_class`

v1.2 열거형은 다음과 같이 정렬됩니다:

`public < internal < confidential < restricted`

에이전트 권한은 `oamp_sensitivity_max`를 포함합니다. 유효한 `sensitivity_class`가 권한 한도를 초과하는 항목은 필터링되거나 거부됩니다.

`governance`가 없을 경우, 유효한 클래스는 강제 목적을 위해 `internal`입니다.

### 3.2 `governance.labels`

v1.3은 강제에 의해 사용되는 계층적 레이블 규칙을 도입합니다.

- 레이블은 `^[a-z][a-z0-9]*(\\.[a-z][a-z0-9_]*)*$`와 일치하는 점이 있는 소문자 ASCII 경로여야 합니다.
- 계층적 접두사 일치가 적용됩니다.
- `health`에 대한 권한은 `health.condition` 및 `health.condition.diagnosis`와 일치합니다.

공급업체 간 상호 운용성을 위한 예약된 최상위 레이블:

- `identity`
- `location`
- `health`
- `finance`
- `relationships`
- `work`
- `preferences`
- `creative`
- `beliefs`
- `behaviour`

공급업체 특정 확장은 `x.<vendor>.<...>` 아래에 있어야 합니다.

계층적 규칙과 일치하지 않는 레이블은 유효한 설명적 v1.2 레이블로 남아 있지만, v1.3을 강제하는 백엔드는 이를 불투명한 정확한 일치 값으로 처리해야 합니다.

`governance.labels`가 없거나 비어 있을 경우, 유효한 레이블 집합은 강제 목적을 위해 `["behaviour"]`입니다.

### 3.3 `governance.handling`

v1.2의 `handling` 힌트는 v1.3에서 하중을 지닙니다:

- `retrieval: "governed"`는 읽기 경로가 권한 필터링을 적용해야 함을 의미합니다.
- `retrieval: "ungoverned"`는 항목이 읽기 경로 필터링에서 면제됨을 의미합니다.
- `export: "governed"`는 내보내기 경로가 권한 필터링을 적용해야 함을 의미합니다.
- `export: "ungoverned"`는 항목이 내보내기 경로 필터링에서 면제됨을 의미합니다.
- `stream: "governed"`는 v1.1 스트리밍 경로가 권한 필터링을 적용해야 함을 의미합니다.
- `stream: "ungoverned"`는 항목이 스트림 필터링에서 면제됨을 의미합니다.

`governance`가 존재하고 처리 값이 생략된 경우, 해당 표면에 대한 유효한 기본값은 `governed`입니다.

---

## 4. 에이전트 권한 주장

### 4.1 JWT 주장 형식

베어러 인증이 JWT를 사용할 때, 토큰은 다음과 같은 추가 주장을 포함합니다:

```json
{
  "sub": "user-abc",
  "oamp_agent_id": "medical-assistant-v3",
  "oamp_grant_id": "grant-2026-05-07-001",
  "oamp_read_labels": ["health", "preferences"],
  "oamp_write_labels": ["health", "preferences"],
  "oamp_sensitivity_max": "restricted",
  "oamp_export_full": false,
  "exp": 1746662400
}
```

| 주장 | 요구 사항 | 설명 |
|-------|-------------|-------------|
| `oamp_agent_id` | MUST | 호출 에이전트에 대한 안정적인 식별자 |
| `oamp_grant_id` | MUST | 권한 인스턴스에 대한 안정적인 식별자 |
| `oamp_read_labels` | MUST | 에이전트가 읽을 수 있는 레이블 |
| `oamp_write_labels` | MUST | 에이전트가 쓸 수 있는 레이블 |
| `oamp_sensitivity_max` | MUST | 읽을 수 있는/쓸 수 있는 가장 높은 민감도 클래스 |
| `oamp_export_full` | MAY | 전체 필터링되지 않은 내보내기가 허가되었는지 여부 |

빈 `oamp_read_labels`는 아무것도 읽지 않음을 의미합니다.

### 4.2 `OAMP-Grant` 헤더

JWT 베어러 토큰을 사용하지 않는 배포의 경우, 동일한 주장 객체는 `OAMP-Grant` 헤더에서 전달될 수 있습니다. 헤더 값은 주장 객체에 대한 압축된 JWS여야 합니다.

### 4.3 Provenance 바인딩

v1.3 권한 하에 쓰기가 발생할 때, 백엔드는 다음을 확인해야 합니다:

- `entry.source.agent_id == oamp_agent_id`, `source.agent_id`가 존재할 때

`provenance.sources[*].agent_id`가 있는 항목의 경우, 백엔드는 호출 권한 또는 로컬 신뢰 모델에 대해 나열된 각 `agent_id`를 검증해야 합니다.

---

## 5. 백엔드 강제 규칙

`governance.enforcement.supported: true`를 광고하는 백엔드는 이러한 규칙을 적용해야 합니다.

### 5.1 읽기 필터링

항목은 다음 조건을 모두 만족할 때만 관리된 읽기를 통과합니다:

1. 유효한 검색 처리 방식이 면제되지 않아야 하며,
2. 적어도 하나의 유효한 항목 레이블이 일부 부여된 읽기 레이블과 일치해야 하며,
3. 유효한 민감도 클래스가 `oamp_sensitivity_max`보다 작거나 같아야 합니다.

실패한 항목은 다음에 나타나서는 안 됩니다:

- `GET /v1/knowledge/{id}`
- `GET /v1/knowledge`
- 검색 응답
- `POST /v1/export`
- v1.1 스트림 전달

### 5.2 존재 숨기기

범위를 벗어난 항목은 에이전트 표면에서 숨겨져야 합니다.

- 범위를 벗어난 ID에 대해 `GET /v1/knowledge/{id}`는 `404 Not Found`를 반환해야 하며, `403 Forbidden`을 반환해서는 안 됩니다.
- 필터링된 항목은 응답 총계에 기여해서는 안 됩니다.

### 5.3 쓰기 거부

`POST /v1/knowledge`는 다음과 같은 경우 `403 Forbidden`으로 거부되어야 합니다:

- 항목의 유효한 레이블이 쓰기 권한을 벗어난 경우, 또는
- 항목의 유효한 민감도 클래스가 `oamp_sensitivity_max`를 초과하는 경우, 또는
- `source.agent_id`가 `oamp_agent_id`와 충돌하는 경우

### 5.4 가져오기 거부

`POST /v1/import`는 쓰기 권한을 초과하는 항목을 거부해야 하며, 이를 가져오기 응답의 `rejected` 필드에 포함해야 합니다.

### 5.5 내보내기 필터링

`POST /v1/export`는 권한 하에 읽을 수 있는 항목만 반환해야 하며, `oamp_export_full`이 존재하고 직접 사용자 인증 하에 허가된 경우를 제외합니다.

### 5.6 스트림 필터링

백엔드가 v1.1 스트리밍을 지원하는 경우, 다음을 수행해야 합니다:

- 범위를 벗어난 항목에 대해 `knowledge_created` 및 `knowledge_updated`를 생략해야 합니다.
- 에이전트가 읽을 수 없는 항목에 대해 `knowledge_deleted`를 생략해야 합니다.

---

## 6. 기능 추가

v1.3은 v1.2 거버넌스 기능 블록을 확장합니다:

```json
{
  "oamp_version": "1.3.0",
  "capabilities": {
    "governance": {
      "supported": true,
      "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
      "labels_supported": true,
      "extended_provenance_supported": true,
      "withheld_stub_support": false,
      "enforcement": {
        "supported": true,
        "spec_version": "1.3.0",
        "label_hierarchy": "dotted-prefix",
        "reserved_top_level_labels": [
          "identity", "location", "health", "finance",
          "relationships", "work", "preferences",
          "creative", "beliefs", "behaviour"
        ],
        "grant_transport": ["jwt-claims", "oamp-grant-header"],
        "existence_hiding": true,
        "stream_filtering": true,
        "export_full_supported": true
      }
    }
  }
}
```

| 필드 | 유형 | 요구 사항 | 설명 |
|-------|------|-------------|-------------|
| `enforcement.supported` | boolean | MUST if `enforcement` present | 백엔드가 v1.3 강제 규칙을 적용합니다. |
| `enforcement.spec_version` | string | MUST | 구현된 v1.3 사양 라인 |
| `enforcement.label_hierarchy` | string | MUST | 이 초안에 대한 `dotted-prefix` |
| `enforcement.reserved_top_level_labels` | array of string | MUST | 예약된 상호 운용 가능한 최상위 레이블 |
| `enforcement.grant_transport` | array of string | MUST | 지원되는 권한 전송 메커니즘 |
| `enforcement.existence_hiding` | boolean | MUST | 범위를 벗어난 ID가 404로 숨겨지는지 여부 |
| `enforcement.stream_filtering` | boolean | MUST | v1.1 스트림이 필터링되는지 여부 |
| `enforcement.export_full_supported` | boolean | MUST | 전체 내보내기 주장이 존중되는지 여부 |

---

## 7. 감사 로그 추가

감사 작업 어휘가 다음을 추가합니다:

- `grant_issue`
- `grant_revoke`
- `scope_denied_read`
- `scope_denied_write`

`scope_denied_read`는 보호된 항목 내용을 기록해서는 안 되며, 에이전트 표면에서 필터링된 항목 ID를 기록하는 것을 피해야 합니다.

---

## 8. 호환성 규칙

### 8.1 v1.3 백엔드

- v1.0, v1.1 및 v1.2 문서를 계속 수용해야 합니다.
- v1.2 `governance` 및 `provenance`를 보존해야 합니다.
- 강제 지원을 정확하게 광고해야 합니다.

### 8.2 v1.0-v1.2 클라이언트

- 이해하지 못하는 경우 `governance.enforcement` 블록을 무시할 수 있습니다.
- `1.3.0` 버전 문자열만으로 휴대 가능한 withheld-result 의미론을 유추해서는 안 됩니다.

### 8.3 권한 없는 토큰

에이전트 표면에 대해 v1.3을 강제하는 백엔드에서, 사용 가능한 `oamp_read_labels`가 없는 토큰은 아무것도 읽지 않는 것으로 처리해야 합니다.

배포는 여전히 휴대 가능한 권한 형식 외부에서 별도의 직접 사용자 인증 경로를 제공할 수 있습니다.

---

## 9. 스키마 및 OpenAPI 아티팩트

v1.3 초안은 다음으로 표현됩니다:

- `spec/v1.3/knowledge-entry.schema.json`
- `spec/v1.3/knowledge-store.schema.json`
- `spec/v1.3/openapi.yaml`

항목 및 저장소 스키마는 v1.2에 대해 추가적입니다. v1.3의 주요 참신함은 강제 기능 계약 및 이 초안에서 정의된 규범적 백엔드 동작입니다.