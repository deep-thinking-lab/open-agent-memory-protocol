# 오픈 에이전트 메모리 프로토콜 — v1.2를 위한 관리 메모리

**상태:** 안정적  
**날짜:** 2026-05-09  
**저자:** Jonathan Conway (Deep Thinking)  
**관련 구현:** `cosmictron`, `kizuna-mem`, `ultra`, `toraeru`  
**의존성:** `spec/v1/oamp-v1.md`, `spec/v1.1/oamp-v1.1.md`

---

## 1. 왜 이것이 존재하는가

여러 OAMP 백엔드는 이제 1급 관리 메모리가 필요합니다:

- **kizuna-mem**은 기업 수준의 민감도 클래스, 출처 인식 정책 평가 및 구조화된 보류 사유가 필요합니다.
- **cosmictron**은 정책 범위 메모리 및 내보내기/가져오기된 거버넌스 메타데이터에 대한 상호 운용 가능한 처리가 필요합니다.
- **ultra**는 관리 메모리를 소비하고 생성할 것이므로, 공급업체 특정 `metadata.*` 블롭은 백엔드 이식성을 원할 경우 더 이상 충분하지 않습니다.
- **toraeru**는 OAMP와 통합될 것이며, 백엔드 특정 거버넌스 페이로드가 아닌 동일한 이식 가능한 메타데이터 계약이 필요합니다.

현재 OAMP v1.0/v1.1은 관리 메모리 데이터를 `metadata` 내부의 공급업체 확장으로만 운반할 수 있으며, 이는 준수합니다. 그러나:

1. 거버넌스 메타데이터에 대한 표준 형태가 없습니다.
2. 관리 메모리에 대한 표준 기능 광고가 없습니다.
3. 더 풍부한 다중 출처 출처의 이식 가능한 표현이 없습니다.
4. “보류됨” 또는 “편집된 스텁”에 대한 표준 전송 수준 개념이 없습니다.

이 제안은 처음 세 가지를 **부가적인 v1.2 작업**으로 표준화하고, 네 번째는 **v2.0**으로 명시적으로 연기합니다. 현재 v1.x 스키마와 스트리밍 페이로드 규칙은 중단 없는 변경 없이 이식 가능한 편집된 스텁을 허용하지 않기 때문입니다.

---

## 2. 권장 사항 요약

### v1.2에서 표준화

- `KnowledgeEntry`에 대한 선택적 `governance` 객체
- `KnowledgeEntry`에 대한 선택적 `provenance` 확장 객체
- 거버넌스 지원을 위한 `GET /v1/capabilities` 광고
- 검색/스트리밍을 위한 선택적 거버넌스 인식 필터 키
- 관리 메모리 필드 및 왕복 허용 오차에 대한 준수 테스트

### v2.0으로 연기

- 표준화된 편집된/보류된 결과 문서
- 가시적 항목과 보류된 스텁을 혼합할 수 있는 표준화된 REST 응답 형태
- 보류된 지식에 대한 표준화된 스트림 이벤트 유형

---

## 3. 보류된 스텁이 v1.2 변경 사항이 아닌 이유

이 제안은 의도적으로 v1.2에서 보류된 스텁을 표준화하지 않습니다.

이유:

1. v1.0에서 `KnowledgeEntry.content`는 필수이며 비어 있지 않은 문자열이어야 합니다.
2. 검색/목록 응답은 `KnowledgeEntry` 객체의 배열을 중심으로 정의됩니다.
3. v1.1 스트리밍은 `knowledge_created` 및 `knowledge_updated`가 전체 `KnowledgeEntry`를 포함한다고 말합니다.

즉, 다음과 같은 이식 가능한 “스텁”은:

```json
{
  "type": "knowledge_entry",
  "content": null,
  "withheld": true
}
```

현재 v1.x 스키마 용어로는 유효하지 않습니다. `content`를 선택적이거나 널 가능하게 만드는 것은 부가적인 것이 아니라 중단되는 스키마 변경이 될 것입니다.

따라서 올바른 표준 분할은:

- **v1.2:** 거버넌스 메타데이터 및 발견 표준화
- **v2.0:** 보류된 결과 의미 표준화

백엔드는 v2.0 디자인이 도착할 때까지 자체 확장에서 공급업체 특정 보류 동작을 계속 구현할 수 있습니다.

---

## 4. 제안된 v1.2 추가 사항

## 4.1 `KnowledgeEntry`에 대한 선택적 `governance` 필드

새로운 선택적 최상위 필드를 추가합니다:

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

### 제안된 필드 형태

| 필드 | 유형 | 요구 사항 | 설명 |
|------|------|------------|------|
| `governance` | 객체 | MAY | 표준 관리 메모리 메타데이터 |
| `governance.sensitivity_class` | 문자열 | `governance`가 존재할 경우 MUST | `public`, `internal`, `confidential`, `restricted` 중 하나 |
| `governance.labels` | 문자열 배열 | MAY | 백엔드 또는 테넌트 정의 거버넌스 레이블 |
| `governance.handling` | 객체 | MAY | 표면 특정 거버넌스 힌트 |
| `governance.handling.retrieval` | 문자열 | MAY | `governed` 또는 `ungoverned` |
| `governance.handling.export` | 문자열 | MAY | `governed` 또는 `ungoverned` |
| `governance.handling.stream` | 문자열 | MAY | `governed` 또는 `ungoverned` |

### 노트

- 이 필드는 **설명적**이며, 전체 정책 언어가 아닙니다.
- 이는 다른 백엔드와 에이전트에게 지식이 어떻게 분류되었는지를 알려줍니다.
- 접근 제어 평가 규칙을 **표준화하지 않습니다**.
- 백엔드는 표준 `governance` 필드 외에도 더 풍부한 로컬 정책 구조를 `metadata`에 매핑할 수 있습니다.

## 4.2 `KnowledgeEntry`에 대한 선택적 확장 `provenance` 필드

`source`는 그대로 유지하고 선택적 더 풍부한 출처 구조를 추가합니다:

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

### 제안된 필드 형태

| 필드 | 유형 | 요구 사항 | 설명 |
|------|------|------------|------|
| `provenance` | 객체 | MAY | 확장된 계보 메타데이터 |
| `provenance.sources` | 배열 | `provenance`가 존재할 경우 MUST | 정렬된 증거/출처 목록 |
| `provenance.sources[].session_id` | 문자열 | MUST | 출처 세션 식별자 |
| `provenance.sources[].timestamp` | 문자열 | MUST | ISO 8601 획득 시간 |
| `provenance.sources[].agent_id` | 문자열 | MAY | 출처 에이전트 식별자 |
| `provenance.sources[].turn_id` | 문자열 | MAY | 턴/메시지 로컬 식별자 |
| `provenance.derived` | 불리언 | MAY | 이 항목이 여러 출처에서 합성되었는지 여부 |

### 노트

- `source`는 필수이며 최소한의 출처 계약으로 유지됩니다.
- `provenance`는 병합, 합성 또는 증거 체인을 지원하는 백엔드를 위한 더 풍부한 상호 운용 가능한 계보 확장입니다.

## 4.3 거버넌스 기능 광고

`/v1/capabilities.capabilities` 아래에 선택적 `governance` 객체를 추가합니다:

```json
{
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

### 제안된 필드

| 필드 | 유형 | 요구 사항 | 설명 |
|------|------|------------|------|
| `governance.supported` | 불리언 | `governance`가 존재할 경우 MUST | 백엔드가 표준화된 거버넌스 필드를 이해함 |
| `governance.sensitivity_classes` | 문자열 배열 | MUST | 백엔드에서 수용하는 클래스 |
| `governance.labels_supported` | 불리언 | MUST | 자유 형식의 거버넌스 레이블이 저장/보존되는지 여부 |
| `governance.extended_provenance_supported` | 불리언 | MUST | `provenance`가 저장/보존되는지 여부 |
| `governance.withheld_stub_support` | 불리언 | MUST | 백엔드에 비표준 보류 스텁 동작이 있는지 여부 |

`withheld_stub_support`는 v1.2에서만 정보적입니다. 이는 표준화된 전송 형식을 의미하지 않습니다.

## 4.4 선택적 거버넌스 인식 필터

백엔드가 필터 광고를 지원하는 경우, 이러한 선택적 키를 표준화합니다:

| 키 | 유형 | 의미 |
|----|------|------|
| `sensitivity_class` | 문자열 배열 | `governance.sensitivity_class`가 집합에 있는 항목과 일치 |
| `governance_label` | 문자열 배열 | 나열된 거버넌스 레이블 중 하나 이상을 포함하는 항목과 일치 |

이는 다음에 적용됩니다:

- REST 검색, 백엔드 특정 쿼리 모델에서 지원되는 경우
- 스트리밍이 지원되는 경우 `streaming.filter_keys`

이 키는 모든 백엔드가 거버넌스 메타데이터를 인덱싱하지 않기 때문에 선택적입니다.

---

## 5. 스키마 및 OpenAPI 영향

이 제안은 현재 v1.0 JSON 스키마가 `KnowledgeEntry` 및 `KnowledgeStore` 항목에 대해 `additionalProperties: false`를 설정하고 있기 때문에 새로운 마이너 버전 스키마가 필요합니다.

따라서 v1.2 작업에는 다음이 포함되어야 합니다:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

부가적인 선택적 필드:

- `governance`
- `provenance`

v1.2에서 필수 필드 변경은 없습니다.

---

## 6. 호환성 규칙

### v1.2 백엔드 동작

- v1.0 및 v1.1 문서를 수용해야 합니다.
- 제공된 경우 `governance` 및 `provenance`를 보존해야 하며, 문서화된 정책 또는 저장 제약이 이를 명시적으로 거부하지 않는 한 보존해야 합니다.
- 이전과 같이 알 수 없는 추가 공급업체 메타데이터는 무시해야 합니다.

### v1.0 / v1.1 클라이언트 동작

- v1.0 또는 v1.1 클라이언트는 이해하지 못하는 경우 `governance` 및 `provenance`를 무시할 수 있습니다.
- 이는 두 필드가 선택적 부가 필드이기 때문에 안전합니다.

### 가져오기/내보내기 기대 사항

- 거버넌스를 지원하는 백엔드는 내보내기/가져오기 시 표준화된 거버넌스 필드를 보존해야 합니다.
- 거버넌스를 지원하지 않는 백엔드는 여전히 문서를 수용하고 필드를 불투명 데이터로 보존하거나 삭제되었다고 문서화해야 합니다.

---

## 7. v1.2의 비목표

다음은 이 제안의 범위에서 명시적으로 제외됩니다:

- 표준화된 허용/거부 정책 언어
- 크로스 백엔드 권한 부여 의미
- 표준화된 `withholding_reason`
- 표준화된 편집된 `KnowledgeEntry` 스텁 형태
- 다중 사용자 구독 의미

이들은 다음이 필요합니다:

- 별도의 v2.0 디자인, 또는
- 현재 v1.x 기대에 맞지 않는 새로운 비 `KnowledgeEntry` 응답/이벤트 봉투.

---

## 8. 준수 추가 사항

v1.2가 도착하면 다음에 대한 준수 사례를 추가합니다:

- `POST /v1/knowledge`가 `governance`를 수용
- `POST /v1/knowledge`가 `provenance`를 수용
- `GET /v1/knowledge/:id`가 표준화된 거버넌스 필드를 왕복
- `POST /v1/import`가 지원되는 경우 거버넌스/출처를 보존
- `/v1/capabilities`가 거버넌스 지원을 정확하게 광고

v1.2에서 보류된 스텁 준수 테스트를 **추가하지 마십시오**.

---

## 9. 제안된 업스트림 문제 분해

### 문제 1: 관리 메모리 범위 분할 비준

결정하고 문서화합니다:

- v1.2는 거버넌스 메타데이터 + 발견을 표준화합니다.
- v2.0은 보류/편집된 결과 의미를 처리합니다.

### 문제 2: v1.2 스키마에 `governance` 및 `provenance` 추가

파일:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`
- 참조 유형 라이브러리

### 문제 3: 기능 광고 및 필터 키

파일:

- `spec/v1.2/oamp-v1.2.md`
- `spec/v1.2/openapi.yaml`
- 재사용되거나 대체된 경우 v1.1 기능 텍스트

### 문제 4: 준수 스위트 범위

파일:

- `reference/compliance/README.md`
- `reference/compliance/src/oamp_compliance/tests/`

### 문제 5: 참조 백엔드 지원

파일:

- `reference/server/`
- 언어 참조 유형

### 문제 6: 보류된 결과에 대한 v2.0 RFC

다음에 대한 별도의 디자인 트랙을 엽니다:

- 중단 없는 봉투 옵션 대 주요 버전 스키마 변경
- 정책에 의해 보류된 REST 의미
- 보류된 업데이트에 대한 스트림 의미
- `withholding_reason`의 이식성

---

## 10. 권장 사항

이 제안을 작업 방향으로 채택합니다:

1. v1.2에서 관리 메모리 메타데이터를 표준화합니다.
2. v1.2에서 더 풍부한 출처를 표준화합니다.
3. 보류/편집 의미를 v1.2에서 제외합니다.
4. 이식 가능한 보류된 결과를 위한 별도의 v2.0 RFC를 엽니다.

이로 인해 `cosmictron`, `kizuna-mem`, `ultra`, 및 `toraeru`는 현재 v1.x `KnowledgeEntry` 형태가 우리가 원하는 모든 관리 메모리 동작을 이미 표현할 수 있다고 가장하지 않고도 공통의 상호 운용 가능한 목표를 갖게 됩니다.