# 오픈 에이전트 메모리 프로토콜 — 버전 1.1.0

**상태:** 안정적  
**날짜:** 2026-05-09  
**저자:** Jonathan Conway (Deep Thinking)  
**대체:** 없음 — v1.0.0을 추가적으로 확장  
**저장소:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 초록

OAMP v1.1은 v1.0.0에 대한 **엄격히 추가적인** 마이너 버전입니다. 이는 v1.0이 의도적으로 "미래 고려 사항"으로 미뤘던 두 가지 OPTIONAL 기능을 정의합니다:

- 클라이언트가 WebSocket을 통해 실시간으로 `KnowledgeEntry` 및 `UserModel` 이벤트를 수신할 수 있는 **스트리밍 구독 전송**.
- 클라이언트가 과거의 특정 시점에서 메모리 상태를 쿼리할 수 있도록 하는 **이중 시간 `as_of` 쿼리 매개변수**.

v1.1을 준수하는 백엔드는 여전히 모든 v1.0 요구 사항을 충족해야 합니다. 두 가지 새로운 기능은 작은 **기능 발견 엔드포인트**를 통해 광고되므로 v1.0 클라이언트는 상호 운용성을 유지합니다. v1.1은 파괴적인 스키마나 엔드포인트 변경을 도입하지 않으며, v1.0 클라이언트는 v1.1 백엔드와 전선 호환성을 유지합니다.

이들을 "v2.0 범위"에서 v1.1 OPTIONAL로 승격시키는 동기는 실용적입니다: 참조 구현(코스믹트론, 키즈나-멤)은 유용한 제품 표면을 제공하기 위해 두 가지 기능이 필요하며, 이들에 대한 OPTIONAL 사양이 없으면 생태계가 정렬될 기회도 없이 호환되지 않는 공급업체 확장이 발생합니다.

이 문서의 "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", 및 "OPTIONAL"이라는 키워드는 [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt)에서 설명된 대로 해석되어야 합니다.

---

## 1. v1.0과의 관계

v1.1은 수정 없이 **모든** v1.0 스키마, 엔드포인트, 요구 사항 및 의미론을 재사용합니다. §3 및 §4의 추가 사항만이 새롭습니다. 문서는 v1.1 전용 필드를 사용할 때만 `oamp_version`을 `"1.1.0"`으로 설정해야 하며, 그렇지 않으면 `"1.0.0"`이 여전히 올바르고 이식성을 위해 선호됩니다.

v1.1 백엔드는 `oamp_version`이 `"1.0.0"` 또는 `"1.1.0"`인 문서를 수락해야 합니다. v1.0 백엔드는 이해하지 못하는 v1.1 전용 필드를 포함하는 `"1.1.0"` 문서를 거부해야 합니다( v1.0 §10.2 — 주요 버전 호환성 규칙에 따라); 그러나 v1.1이 새로운 최상위 필드를 도입하지 않기 때문에, v1.0 백엔드는 버전 레이블을 무시하고 v1.0 필드만 포함하는 `"1.1.0"` 문서를 수락해야 합니다.

---

## 2. 기능 발견

v1.1은 클라이언트가 백엔드가 지원하는 OPTIONAL 기능을 발견할 수 있는 단일 새로운 엔드포인트를 도입합니다.

### 2.1 GET `/v1/capabilities`

백엔드의 프로토콜 표면을 설명하는 JSON 객체를 반환합니다.

**응답:**

```json
{
  "oamp_version": "1.1.0",
  "capabilities": {
    "streaming": {
      "supported": true,
      "subprotocol": "oamp.v1",
      "endpoint": "/v1/stream",
      "event_types": ["knowledge_created", "knowledge_updated",
                      "knowledge_deleted", "user_model_updated"]
    },
    "as_of": {
      "supported": true,
      "endpoints": ["/v1/knowledge", "/v1/knowledge/{id}",
                    "/v1/user-model/{user_id}"],
      "min_resolution_ms": 1
    },
    "user_id_format": {
      "description": "tenant:node composite (e.g. '1:user')",
      "pattern": "^[0-9]+:.+$"
    },
    "id_preservation": "preserved",
    "content_types": ["application/json", "application/protobuf"],
    "auth_schemes": ["bearer"]
  }
}
```

**요구 사항:**

- v1.1을 광고하는 백엔드는 이 엔드포인트를 구현해야 합니다.
- 모든 `capabilities.*.supported` 필드는 boolean이어야 합니다.
- 클라이언트는 이 엔드포인트를 연결 수명 동안 최대 한 번 호출하고 결과를 캐시해야 합니다.
- 백엔드는 `capabilities.metadata`(객체) 아래에 공급업체 특정 키를 포함할 수 있습니다. 클라이언트는 알 수 없는 키를 용인해야 합니다.

**`user_id_format` (REQUIRED):**

백엔드는 클라이언트가 여러 OAMP 백엔드를 연결할 수 있도록 `user_id` 인코딩 형식을 광고해야 합니다. 객체는 다음을 포함합니다:

| 필드 | 유형 | 요구 사항 | 설명 |
|-------|------|-------------|-------------|
| `description` | string | MUST | 형식에 대한 사람이 읽을 수 있는 설명 (예: `"tenant:node composite (e.g. '1:user')"`, `"64-char lowercase hex Ed25519 public key"`). |
| `pattern` | string | MAY | 이 백엔드의 유효한 `user_id` 값을 일치시키는 ECMA-262 정규 표현식. 클라이언트는 이를 사전 검증에 사용할 수 있습니다. |

OAMP 문서의 `user_id` 필드는 불투명한 문자열로 남아 있으며(스키마에 형식 제약 없음), 기능 광고는 클라이언트 측 호환성 검사를 위한 것입니다. 호환되지 않는 `user_id` 형식을 가진 백엔드를 연결하는 클라이언트는 교차 백엔드 전송 중에 `user_id` 값을 변환해야 합니다(이는 클라이언트의 책임이며 백엔드의 책임이 아닙니다).

**`id_preservation` (REQUIRED):**

`POST /v1/import` 중에 클라이언트가 제공한 항목 ID를 백엔드가 보존하는지 여부를 나타내는 문자열입니다. 다음 중 하나:

- `"preserved"` -- 백엔드는 클라이언트가 제공한 `id`를 변경하지 않고 저장하고 반환합니다. 가져오기 응답의 `id_mappings` 필드는 항상 비어 있습니다 `{}`.
- `"regenerated"` -- 백엔드는 가져온 항목에 새 ID를 할당할 수 있습니다(예: 내부 키에서 결정론적으로 파생). 가져오기 응답의 `id_mappings` 필드는 각 원래 ID에서 새로 할당된 ID로의 매핑을 포함해야 합니다.

여러 OAMP 백엔드를 연결하고 항목 ID를 조인 키로 사용하는 클라이언트는 `id_preservation`을 검사해야 하며, `"regenerated"`인 경우 가져오기 응답의 `id_mappings`를 적용하여 참조 무결성을 유지해야 합니다.

### 2.2 v1.0 이전 호환성

v1.0 백엔드는 `/v1/capabilities`에 대해 `404 Not Found`를 반환합니다. 클라이언트는 이 응답을 "백엔드는 v1.0이다; 사용할 수 있는 OPTIONAL 기능이 없다"로 간주하고 REST 전용 동작으로 돌아가야 합니다. v1.0 백엔드는 또한 `user_id_format`이나 `id_preservation`을 광고하지 않으므로, 여러 백엔드를 연결하는 클라이언트는 이를 우아하게 처리해야 합니다(§5 참조).

### 2.3 가져오기 응답 형태 (v1.0 §6.4의 명확화)

v1.0 §6.4는 `POST /v1/import`가 "`200 OK`와 요약"을 반환한다고 정의했지만 상태 코드나 응답 본문의 형태를 고정하지 않았습니다. v1.1은 다음을 의무화합니다:

**상태 코드:** `201 Created`. (클라이언트는 또한 v1.0 백엔드에서의 `200 OK`를 호환성을 위해 수락해야 합니다.)

**응답 본문:**

```json
{
  "imported": 5,
  "skipped": 0,
  "rejected": 0,
  "id_mappings": {
    "88f88510-928b-49d9-aff1-4f32acbf1f97": "a299eeae-39ac-4248-ae24-007302cb64fc"
  }
}
```

| 필드 | 유형 | 요구 사항 | 설명 |
|-------|------|-------------|-------------|
| `imported` | integer | MUST | 성공적으로 가져온 항목 수. |
| `skipped` | integer | MUST | 건너뛴 항목 수(예: 동일하거나 더 높은 신뢰도로 중복). |
| `rejected` | integer | MUST | 검증 오류로 인해 거부된 항목 수. |
| `id_mappings` | object | MUST | 원래 ID에서 할당된 ID로의 매핑. 모든 ID가 보존된 경우 비어 있습니다 `{}`. §2.4 참조. |
| `rejections` | array | MAY | 거부된 항목에 대한 세부 정보. 각 요소: `{"id": "...", "reason": "..."}`. |

### 2.4 가져오기 시 항목 ID 보존 (v1.0 §4.4의 명확화)

구현은 가져오는 동안 항목 ID를 보존하거나 재생성할 수 있지만, 가져오기 응답을 통해 결과를 전달해야 합니다:

- **ID 보존 백엔드** (기능에서 `id_preservation: "preserved"`로 광고됨): 클라이언트가 제공한 `id`를 변경하지 않고 저장합니다. 가져오기 응답의 `id_mappings` 필드는 `{}`여야 합니다.
- **ID 재생성 백엔드** (기능에서 `id_preservation: "regenerated"`로 광고됨): 가져오는 동안 새 ID를 할당합니다(예: 결정론적 파생). 가져오기 응답의 `id_mappings` 필드는 모든 가져온 항목의 원래 ID를 새로 할당된 ID로 매핑해야 합니다.

이것은 내부 설계를 변경하지 않고도 두 가지 아키텍처 패턴을 수용합니다. ID 안정성에 의존하는 클라이언트(예: 항목 ID로 키가 지정된 메모리 그래프를 구축하는 에이전트)는 `id_mappings`를 검사하고 가져오기 후 참조를 업데이트해야 합니다.

---

## 3. 스트리밍 전송 (OPTIONAL)

### 3.1 동기

OAMP v1.0은 폴링 기반입니다: 클라이언트는 메모리 변경 사항에 대해 검색 쿼리를 재발행하여 알게 됩니다. 대화형 에이전트, 관찰 가능성 표면 및 대시보드의 경우 이는 높은 폴링 부하 또는 오래된 UI를 생성합니다. v1.1은 클라이언트가 발생하는 메모리 변화를 구독할 수 있는 WebSocket 하위 프로토콜을 정의합니다.

이는 (a) 모든 백엔드가 실시간 이벤트 소스를 갖고 있는 것은 아니며, (b) v1.0의 폴링 모델이 배치 에이전트에 대해 여전히 올바르고 충분하기 때문에 OPTIONAL입니다.

### 3.2 엔드포인트

스트리밍 지원이 있는 v1.1 백엔드는 다음을 노출해야 합니다:

- **URL:** `wss://{host}/v1/stream` (비 TLS 개발의 경우 `ws://`)
- **하위 프로토콜:** `oamp.v1` (표준 WebSocket `Sec-WebSocket-Protocol` 헤더를 통해 협상됨)

클라이언트가 하위 프로토콜 목록에서 `oamp.v1`을 요청하지 않으면 백엔드는 HTTP `400 Bad Request`로 업그레이드를 거부해야 합니다.

### 3.3 인증

WebSocket 업그레이드는 REST API와 동일한 방식으로 인증해야 합니다. 백엔드는 업그레이드 요청의 `Authorization` 헤더를 통해 베어러 토큰을 수락해야 하며, WebSocket 업그레이드에서 헤더를 설정할 수 없는 브라우저 클라이언트를 위해 `?token=` 쿼리 매개변수로 수락할 수 있습니다. 선택한 스킴은 `/v1/capabilities`에서 선언해야 합니다.

### 3.4 프레임 형식

모든 프레임은 단일 JSON 객체를 포함하는 **텍스트 프레임**입니다. (이진 프레임은 향후 protobuf 모드 스트리밍을 위해 예약되어 있으며 v1.1에서 사용되어서는 안 됩니다.)

모든 프레임은 다음 형태를 가집니다:

```json
{
  "oamp_version": "1.1.0",
  "type": "<frame_type>",
  "id": "<uuid_v4>",
  "ts": "<iso8601>",
  "payload": { ... }
}
```

`id`는 클라이언트가 응답을 상관시키는 데 사용하는 프레임별 식별자입니다; `ts`는 프레임이 방출된 순간의 백엔드의 단조 타임스탬프입니다.

### 3.5 클라이언트 → 서버 프레임

| `type`         | 목적                                            |
|----------------|----------------------------------------------------|
| `subscribe`    | 필터와 함께 구독을 엽니다.                  |
| `unsubscribe`  | 이전에 열린 구독을 닫습니다.            |
| `ping`         | 생존 확인; 백엔드는 `pong`으로 응답해야 합니다.  |

**`subscribe` 페이로드:**

```json
{
  "subscription_id": "<client-chosen-string>",
  "user_id": "user-123",
  "event_types": ["knowledge_created", "knowledge_updated"],
  "filters": {
    "category": ["preference", "correction"],
    "tags": ["language"]
  },
  "include_initial_snapshot": false
}
```

- `subscription_id`는 클라이언트가 선택하며 연결당 고유해야 합니다. 서버는 이후의 모든 이벤트 및 구독 해제 확인에서 이를 사용합니다.
- `user_id`는 REQUIRED입니다. 백엔드는 교차 사용자 구독을 거부해야 합니다( `error` 프레임을 반환하며 코드 `"forbidden"`).
- `event_types`는 백엔드가 지원하는 모든 이벤트 유형을 구독하기 위해 생략할 수 있습니다.
- `filters`는 OPTIONAL입니다; 인식된 필터 키는 §3.7에 나열되어 있습니다. 알 수 없는 필터 키는 무시해야 하며 거부해서는 안 됩니다.
- `include_initial_snapshot` (기본값 `false`): `true`인 경우, 백엔드는 라이브 이벤트가 흐르기 전에 현재 일치하는 상태를 포함하는 하나의 `knowledge_snapshot` 프레임을 방출해야 합니다.

### 3.6 서버 → 클라이언트 프레임

| `type`                | 목적                                              |
|-----------------------|------------------------------------------------------|
| `subscribed`          | 구독을 확인합니다.                          |
| `unsubscribed`        | 구독 해제를 확인합니다.                       |
| `knowledge_created`   | 새로운 `KnowledgeEntry`가 저장되었습니다.                   |
| `knowledge_updated`   | 기존 `KnowledgeEntry`가 수정되었습니다 (PATCH).   |
| `knowledge_deleted`   | `KnowledgeEntry`가 영구적으로 삭제되었습니다.          |
| `knowledge_snapshot`  | `include_initial_snapshot`에 대한 일회성 스냅샷입니다.    |
| `user_model_updated`  | `UserModel` 행이 업데이트되었습니다.                       |
| `error`               | 프로토콜 또는 애플리케이션 오류입니다.                     |
| `pong`                | 생존 응답입니다.                                      |

**`knowledge_created` 페이로드:**

```json
{
  "subscription_id": "<echoed-from-subscribe>",
  "entry": { /* 전체 v1.0 KnowledgeEntry 문서 */ }
}
```

`knowledge_updated`는 **업데이트 후** 항목을 포함합니다. `knowledge_deleted`는 v1.0의 "로그에 내용 없음" 규칙을 충족하기 위해 `{ "subscription_id": "...", "id": "<uuid>", "user_id": "..." }`만 포함하여 삭제된 내용을 재전송해서는 안 됩니다.

**`error` 페이로드:**

```json
{
  "subscription_id": "<id-or-null>",
  "code": "forbidden | invalid | rate_limited | internal",
  "message": "사람이 읽을 수 있는",
  "retryable": false
}
```

### 3.7 인식된 필터 키

| 키        | 유형            | 의미                                  |
|------------|-----------------|--------------------------------------------|
| `category` | 문자열 배열 | 이 v1.0 카테고리 중 하나와 일치합니다.        |
| `tags`     | 문자열 배열 | 항목은 나열된 태그 중 하나 이상을 포함해야 합니다.|
| `min_confidence` | 숫자    | 항목의 `confidence`는 이 값 이상이어야 합니다. |

백엔드는 추가 필터 키를 지원할 수 있으며, 이는 `/v1/capabilities.streaming.filter_keys`에서 광고해야 합니다.

### 3.8 백프레셔 및 전달

- 프로토콜은 **최대 한 번**입니다. 클라이언트가 따라잡을 수 없는 경우, 백엔드는 이벤트를 드롭할 수 있으며 `"rate_limited"` 코드와 `retryable: true`로 단일 `error` 프레임을 방출하여 간격을 신호해야 합니다. 정확히 한 번의 의미론이 필요한 클라이언트는 `/v1/knowledge` 폴링을 통해 조정해야 합니다.
- 백엔드는 클라이언트 트래픽이 60초 동안 없으면 WebSocket을 닫아야 합니다( `ping` 없음, 다른 프레임 없음). 클라이언트는 30초마다 `ping`을 보내야 합니다.
- 백엔드는 연결당 최소 16개의 동시 구독을 용인해야 합니다.

### 3.9 개인 정보 보호

v1.0 §8 개인 정보 보호 규칙은 스트리밍된 콘텐츠에 REST 응답인 것처럼 적용됩니다:

- 지식 콘텐츠는 연결의 어느 쪽에서도 기록되어서는 안 됩니다.
- `knowledge_deleted` 프레임은 삭제된 내용을 포함해서는 안 됩니다.
- 구독은 단일 `user_id`로 범위가 지정되어야 합니다. 다중 사용자 팬아웃은 v2.0의 문제입니다.

---

## 4. 이중 시간 `as_of` 쿼리 매개변수 (OPTIONAL)

### 4.1 동기

많은 메모리 백엔드(코스믹트론, 키즈나-멤 등)는 이미 이중 시간 데이터를 저장하고 있습니다 — `valid_time` 축(사실이 세계에서 진실했을 때)과 `ingest_time` 축(시스템이 사실을 알게 된 때). v1.0은 "T 시점에 무엇을 알고 있었습니까?"라고 물어볼 방법이 없으며, 이는 다음과 같은 경우에 필요합니다:

- 에이전트 결정의 재생 및 디버깅.
- 준수 감사("이 결정이 내려졌을 때 파일에 무엇이 있었습니까?").
- 관찰 가능성 대시보드에서의 역시간 여행 UI.

v1.1은 이 저장 기능을 노출하는 단일 보편적으로 적용 가능한 쿼리 매개변수를 정의하며, 내부 표현을 강제하지 않습니다.

### 4.2 매개변수

`as_of` 지원이 있는 백엔드는 아래 나열된 엔드포인트에서 다음 쿼리 매개변수를 수락해야 합니다:

```
?as_of=<iso8601-datetime>
```

영향을 받는 엔드포인트:

| 엔드포인트                          | `as_of`가 있는 의미론                          |
|-----------------------------------|-------------------------------------------------|
| `GET /v1/knowledge?query=...`     | `as_of` 시점에서 존재했던 인덱스를 검색합니다.      |
| `GET /v1/knowledge/{id}`          | `as_of` 시점에서 항목의 상태를 반환합니다.         |
| `GET /v1/user-model/{user_id}`    | `as_of` 시점에서 사용자 모델을 반환합니다.            |

변경 엔드포인트(`POST`, `PATCH`, `DELETE`)는 `as_of`를 수락해서는 안 되며, 매개변수가 제공되면 `400 Bad Request`로 응답해야 합니다.

### 4.3 의미론

두 가지 의미론 축이 가능합니다. 백엔드는 기본적으로 **ingest_time 의미론**을 선택해야 합니다: "정확히 `as_of`에서 발행된 동일한 쿼리가 반환했을 결과를 보여줍니다." 이것은 보편적으로 잘 정의된 유일한 해석이며, 모든 알려진 참조 백엔드가 구현하는 것입니다.

백엔드가 `valid_time` 쿼리를 지원하는 경우(세계 상태 축), 이를 별도의 명시적으로 명명된 매개변수(예: `?valid_at=`)를 통해 노출해야 합니다. v1.1은 이 목적을 위해 `valid_at`을 예약하지만 표준화하지 않습니다; 이는 v2.0 작업입니다.

### 4.4 응답 형태

응답 본문은 동등한 v1.0 응답과 동일해야 합니다. v1.1은 본문이 설명하는 역사적 상태를 변경합니다.

v1.1을 인식하는 백엔드는 사용한 타임스탬프를 반영하는 응답 헤더 `OAMP-As-Of: <iso8601>`를 포함해야 합니다. 클라이언트는 이를 사용하여 타임스탬프 정규화를 감지할 수 있습니다(예: 백엔드가 저장 해상도로 반올림한 경우).

### 4.5 범위를 벗어난 타임스탬프

- 미래의 `as_of`는 `now`로 처리해야 합니다. 백엔드는 실제로 해결된 타임스탬프에 대해 `OAMP-As-Of`를 설정해야 합니다.
- 사용자의 첫 번째 수집 이벤트 이전의 `as_of`는 빈 결과 집합(HTTP 200)을 반환해야 하며, 404를 반환해서는 안 됩니다.
- 백엔드가 보존/스냅샷 만료로 인해 해결할 수 없는 `as_of`는 `409 Conflict`를 반환해야 하며 `code: "as_of_expired"`를 포함해야 합니다.

### 4.6 기능 광고

`/v1/capabilities.as_of.min_resolution_ms`는 백엔드가 해결할 수 있는 가장 작은 시간 차이를 보고해야 합니다(예: 스냅샷 간격). 클라이언트는 서브 밀리초 해상도를 가정해서는 안 됩니다.

---

## 5. 준수

**v1.1 준수**를 주장하는 백엔드는 다음을 충족해야 합니다:

1. 모든 v1.0 필수 요구 사항을 충족해야 합니다.
2. 진실한 기능 플래그를 반환하는 `GET /v1/capabilities`를 구현해야 합니다.
3. 광고하는 각 OPTIONAL 기능(`streaming`, `as_of`)에 대해:
   §3 또는 §4에 설명된 전체 표면을 구현해야 합니다.
4. 문서화된 HTTP/WebSocket 오류 코드로 지원되지 않는 OPTIONAL 기능을 거부해야 하며, 결코 조용히 무시해서는 안 됩니다.

백엔드는 **지원되는 OPTIONAL 기능이 없는** v1.1 준수를 주장할 수 있습니다. 이는 유용합니다: 클라이언트에게 백엔드가 v1.1 어휘를 이해하고 있으며 `/v1/capabilities`에서 향후 OPTIONAL 기능을 노출할 것임을 신호합니다.

`/validators/validate.sh`의 검증기는 별도의 PR에서 v1.1 고정 장치를 얻을 것이며; v1.1 문서는 변경되지 않은 v1.0 JSON 스키마에 대해 검증해야 합니다.

---

## 6. v1.0 클라이언트를 위한 마이그레이션 경로

v1.1 백엔드와 통신하는 v1.0 클라이언트는 변경 없이 계속 작동합니다. v1.1 기능을 선택하고자 하는 v1.0 클라이언트는:

1. `GET /v1/capabilities`를 발행하고 응답을 검사합니다.
2. `streaming.supported`인 경우, WebSocket을 열고 §3을 따릅니다.
3. `as_of.supported`인 경우, 유용한 읽기 요청에 `?as_of=`를 추가합니다.

저장된 문서에서 `oamp_version`을 올릴 필요는 없습니다. 버전 문자열은 문서를 설명하며 세션을 설명하지 않습니다 — v1.1 클라이언트는 v1.0 문서를 완벽하게 저장할 수 있습니다.

---

## 7. v1.1 최종화를 위한 열린 질문

이들은 v1.1이 안정적으로 표시되기 전에 커뮤니티 논의를 위해 추적됩니다:

1. **재연결 간 구독 재개.** 클라이언트가 `subscribe`에서 `since=<event_id>`를 전달하여 놓친 이벤트를 재생할 수 있어야 합니까? 이는 백엔드가 이벤트 로그를 유지해야 함을 요구합니다; 많은 백엔드가 그렇지 않습니다. *임시 답변:* v2.0에 맡깁니다.
2. **스냅샷 페이지네이션.** 100k 항목을 가진 사용자의 `knowledge_snapshot` 프레임은 오늘날 단일 프레임입니다. 청크화를 의무화해야 합니까? *임시 답변:* 백엔드가 `streaming.snapshot_max_entries` 제한을 보고하면 `snapshot_chunk`를 의무화하고, 그렇지 않으면 단일 프레임으로 합니다.
3. **`valid_at` 표준화.** 금융 및 준수에서의 실제 수요는 `valid_at`이 일부 워크플로우에 대해 `as_of`보다 더 유용하다는 것을 시사합니다. *임시 답변:* v1.1에 `as_of`를 포함하고, `valid_at`은 v1.2 또는 v2.0에서 두 개 이상의 백엔드가 상호 운용 가능한 구현을 제공할 때까지 보류합니다.
4. **gRPC 스트리밍.** 스트리밍 하위 프로토콜에 gRPC 바인딩이 있어야 합니까? *임시 답변:* JSON 형태가 안정화되면 `/proto/` 디렉토리에 `service Stream { rpc Subscribe(stream SubscribeRequest) returns (stream Event); }`가 추가됩니다.

---

## 부록 A: 기능 스키마

`/v1/capabilities` 응답에 대한 JSON 스키마는 §2가 최종화되면 `spec/v1.1/capabilities.schema.json`에 추가될 것입니다. §2.1의 형태는 작업 정의입니다.

## 부록 B: 참조 구현 대상

두 개의 참조 백엔드가 이 초안과 동시에 v1.1 OPTIONAL 기능을 도입할 것입니다:

- **코스믹트론** (Rust) — `/v1/capabilities`, `/v1/oamp/*` REST, `/v1/oamp/stream` WebSocket 하위 프로토콜, 메모리 읽기에서 `?as_of=`. `cosmictron/docs/design/OAMP_TRANSPORT.md`를 참조하십시오.
- **키즈나-멤** (Zig 코어 + Rust 사이드카) — 동일한 표면; Rust 사이드카에서 제공되는 WebSocket. `kizuna-dream/docs/design/OAMP_TRANSPORT.md` 및 `kizuna-dream/docs/design/WEBSOCKET_EVENT_STREAM.md`를 참조하십시오.

이 구현은 사양에 대한 준수 압력 테스트입니다; 둘 중 하나라도 이 초안에 대해 깨끗하게 도착할 수 없다면, v1.1이 최종화되기 전에 초안이 수정될 것입니다.