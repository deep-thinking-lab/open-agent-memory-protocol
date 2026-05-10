# 오픈 에이전트 메모리 프로토콜 — 버전 1.2.0

**상태:** 안정적  
**날짜:** 2026-05-09  
**저자:** 조나단 콘웨이 (딥 씽킹)  
**대체:** 없음 — v1.0.0 및 v1.1.0을 추가적으로 확장  
**저장소:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 초록

OAMP v1.2는 v1.0.0 및 선택적 v1.1 초안 기능에 대한 **엄격히 추가적인** 마이너 버전입니다. 다음에 대한 휴대 가능한 형식을 표준화합니다:

- `KnowledgeEntry`의 관리 메모리 메타데이터,
- `KnowledgeEntry`의 풍부한 다중 출처 출처,
- `GET /v1/capabilities`에서의 거버넌스 기능 광고, 및
- 검색 및 스트리밍 표면을 위한 거버넌스 인식 필터 키.

v1.2는 의도적으로 보류되거나 수정된 결과 문서를 표준화하지 않습니다. 이러한 의미는 새로운 응답 봉투 또는 `KnowledgeEntry` 계약에 대한 파괴적인 변경을 요구하므로, 별도의 v2.0 설계 트랙으로 명시적으로 연기됩니다.

이 문서의 "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", 및 "OPTIONAL"과 같은 키워드는 [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt)에서 설명한 대로 해석되어야 합니다.

---

## 1. v1.0 및 v1.1과의 관계

v1.2는 모든 v1.0 스키마, 엔드포인트, 요구 사항 및 의미를 재사용하며, 선택적 v1.1 기능 모델을 포함하되, 필요한 필드를 변경하지 않습니다.

유일한 새로운 와이어 수준 추가 사항은 다음과 같습니다:

- 선택적 `governance` on `KnowledgeEntry`
- 선택적 `provenance` on `KnowledgeEntry`
- 선택적 `capabilities.governance` on `GET /v1/capabilities`
- 선택적 거버넌스 인식 필터 키

문서는 v1.2 전용 필드를 사용할 때 `oamp_version`을 `"1.2.0"`으로 설정해야 합니다. v1.0 필드만 사용하는 문서는 최대 호환성을 위해 `"1.0.0"`을 계속 사용할 수 있습니다.

---

## 2. 범위 분할

### 2.1 v1.2에서 표준화된 항목

- 휴대 가능한 관리 메모리 메타데이터
- 휴대 가능한 풍부한 출처
- 관리 메모리 지원을 위한 기능 발견
- 선택적 거버넌스 인식 필터링

### 2.2 v2.0으로 명시적으로 연기된 항목

- 표준화된 보류되거나 수정된 결과 문서
- 가시 항목과 보류된 스텁을 포함하는 혼합 결과 집합
- 보류된 지식에 대한 스트림 이벤트 페이로드
- 휴대 가능한 `withholding_reason` 의미
- 표준화된 크로스 백엔드 권한 부여 정책 언어

이 분할은 v1.2 초안에 대해 규범적입니다. 구현은 보류되거나 수정된 스텁이 v1.2에 의해 표준화되었다고 주장해서는 안 됩니다.

---

## 3. `KnowledgeEntry` 추가 사항

### 3.1 선택적 `governance`

`KnowledgeEntry`는 선택적 `governance` 객체를 추가합니다:

```json
{
  "governance": {
    "sensitivity_class": "confidential",
    "labels": ["finance", "hr"],
    "handling": {
      "retrieval": "governed",
      "export": "governed",
      "stream": "governed"
    }
  }
}
```

#### 필드

| 필드 | 유형 | 요구 사항 | 설명 |
|------|------|------------|------|
| `governance` | 객체 | MAY | 표준 관리 메모리 메타데이터 |
| `governance.sensitivity_class` | 문자열 | MUST if `governance` present | `public`, `internal`, `confidential`, `restricted` 중 하나 |
| `governance.labels` | 문자열 배열 | MAY | 백엔드 또는 테넌트 정의의 거버넌스 레이블 |
| `governance.handling` | 객체 | MAY | 표면별 처리 힌트 |
| `governance.handling.retrieval` | 문자열 | MAY | `governed` 또는 `ungoverned` |
| `governance.handling.export` | 문자열 | MAY | `governed` 또는 `ungoverned` |
| `governance.handling.stream` | 문자열 | MAY | `governed` 또는 `ungoverned` |

`governance` 객체는 설명적입니다. 이는 휴대 가능한 정책 엔진이 아닙니다.

### 3.2 선택적 `provenance`

`KnowledgeEntry`는 기존의 필수 `source` 객체를 유지하고 선택적 풍부한 `provenance` 객체를 추가합니다:

```json
{
  "source": {
    "session_id": "sess-42",
    "timestamp": "2026-05-07T10:00:00Z"
  },
  "provenance": {
    "sources": [
      {
        "session_id": "sess-42",
        "timestamp": "2026-05-07T10:00:00Z",
        "agent_id": "agent-a",
        "turn_id": "turn-3"
      },
      {
        "session_id": "sess-43",
        "timestamp": "2026-05-08T09:00:00Z",
        "agent_id": "agent-a",
        "turn_id": "turn-7"
      }
    ],
    "derived": true
  }
}
```

#### 필드

| 필드 | 유형 | 요구 사항 | 설명 |
|------|------|------------|------|
| `provenance` | 객체 | MAY | 확장된 계보 메타데이터 |
| `provenance.sources` | 배열 | MUST if `provenance` present | 정렬된 증거/출처 목록 |
| `provenance.sources[].session_id` | 문자열 | MUST | 출처 세션 식별자 |
| `provenance.sources[].timestamp` | 문자열 | MUST | ISO 8601 획득 시간 |
| `provenance.sources[].agent_id` | 문자열 | MAY | 출처 에이전트 식별자 |
| `provenance.sources[].turn_id` | 문자열 | MAY | 턴/메시지 로컬 식별자 |
| `provenance.derived` | 불리언 | MAY | 이 항목이 여러 출처에서 합성되었는지 여부 |

기존의 `source` 필드는 최소한의 출처 계약으로 남아 있으며 여전히 존재해야 합니다.

---

## 4. 기능 추가 사항

v1.2는 선택적 `capabilities.governance` 객체로 `GET /v1/capabilities` 응답을 확장합니다:

```json
{
  "oamp_version": "1.2.0",
  "capabilities": {
    "governance": {
      "supported": true,
      "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
      "labels_supported": true,
      "extended_provenance_supported": true,
      "withheld_stub_support": false
    }
  }
}
```

| 필드 | 유형 | 요구 사항 | 설명 |
|------|------|------------|------|
| `governance.supported` | 불리언 | MUST if `governance` present | 백엔드가 표준화된 거버넌스 필드를 이해함 |
| `governance.sensitivity_classes` | 문자열 배열 | MUST | 백엔드에서 수용하는 클래스 |
| `governance.labels_supported` | 불리언 | MUST | 자유 형식 레이블이 저장되고 유지되는지 여부 |
| `governance.extended_provenance_supported` | 불리언 | MUST | `provenance`가 저장되고 유지되는지 여부 |
| `governance.withheld_stub_support` | 불리언 | MUST | 백엔드에 비표준 보류 동작이 있는지 여부 |

`withheld_stub_support`는 v1.2에서 정보 제공용으로만 사용되며, 휴대 가능한 결과 형식 보장으로 읽혀서는 안 됩니다.

---

## 5. 거버넌스 인식 필터 키

이미 쿼리 필터 또는 스트리밍 구독 필터를 지원하는 백엔드는 이러한 선택적 거버넌스 인식 키를 광고하고 수용할 수 있습니다:

| 키 | 유형 | 의미 |
|----|------|------|
| `sensitivity_class` | 문자열 배열 | `governance.sensitivity_class`가 집합에 있는 항목과 일치 |
| `governance_label` | 문자열 배열 | 나열된 거버넌스 레이블 중 하나 이상을 포함하는 항목과 일치 |

REST 검색 엔드포인트의 경우, 이러한 키는 반복 쿼리 매개변수로 나타날 수 있습니다. 스트리밍의 경우, 이러한 키는 `streaming.filter_keys` 광고 및 구독 페이로드에 나타날 수 있습니다.

거버넌스 메타데이터를 인덱싱하지 않는 백엔드는 이러한 키를 거부하거나 무시할 수 있지만, 기능에서 지원을 정확하게 광고해야 합니다.

---

## 6. 호환성 규칙

### 6.1 v1.2 백엔드

- v1.0 및 v1.1 문서를 수용해야 합니다.
- 지원되는 경우 `governance` 및 `provenance`를 유지해야 합니다.
- 알려지지 않은 공급업체 특정 메타데이터 확장을 계속 허용해야 합니다.

### 6.2 v1.0 및 v1.1 클라이언트

- 이해하지 못하는 경우 `governance` 및 `provenance`를 무시할 수 있습니다.
- v1.2 버전 문자열만으로 보류되거나 수정된 결과 의미를 가정해서는 안 됩니다.

### 6.3 가져오기 및 내보내기

- 관리 메모리를 지원하는 백엔드는 내보내기 및 가져오기 간에 표준화된 `governance` 및 `provenance`를 유지해야 합니다.
- 관리 메모리를 지원하지 않는 백엔드는 해당 필드가 불투명하게 유지되는지 또는 삭제되는지 문서화해야 합니다.

---

## 7. 스키마 및 OpenAPI 아티팩트

v1.2 초안은 다음으로 표현됩니다:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

이 아티팩트는 `spec/v1/`에 대해 추가적이며 v1.0 필수 필드 계약을 변경하지 않습니다.