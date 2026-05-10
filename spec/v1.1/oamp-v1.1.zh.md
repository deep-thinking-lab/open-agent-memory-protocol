# 开放代理内存协议 — 版本 1.1.0

**状态：** 稳定  
**日期：** 2026-05-09  
**作者：** Jonathan Conway (Deep Thinking)  
**替代：** 无 — 以附加方式扩展 v1.0.0  
**代码库：** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 摘要

OAMP v1.1 是 v1.0.0 的 **严格附加** 小版本。它定义了两个
OPTIONAL 功能，v1.0 故意推迟到“未来考虑”：

- 一个 **流式订阅传输**，允许客户端通过 WebSocket 实时接收
  `KnowledgeEntry` 和 `UserModel` 事件。
- 一个 **双时间 `as_of` 查询参数** 用于读取端点，允许客户端
  查询在过去某个时间点的内存状态。

符合 v1.1 的后端仍然必须满足每个 v1.0 的要求。两个新功能通过一个小的 **能力发现端点** 进行宣传，因此 v1.0 客户端仍然可以互操作。v1.1 不引入破坏性的模式或
端点更改，v1.0 客户端与 v1.1 后端保持线下兼容。

将这些功能从“v2.0 范围”提升到 v1.1 OPTIONAL 的动机是
实际的：参考实现（cosmictron, kizuna-mem）需要这两个
功能以提供有用的产品表面，而缺乏甚至一个
OPTIONAL 规范会在生态系统有机会对齐之前创建不兼容的供应商扩展。

本文档中的关键字 "MUST"、"MUST NOT"、"REQUIRED"、"SHALL"、"SHALL NOT"、"SHOULD"、
"SHOULD NOT"、"RECOMMENDED"、"MAY" 和 "OPTIONAL" 应按照 [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) 中的描述进行解释。

---

## 1. 与 v1.0 的关系

v1.1 重用 **所有** v1.0 模式、端点、要求和语义
而不进行修改。只有第 §3 和 §4 中的新增内容是新的。文档
应仅在使用 v1.1 专用字段时将 `oamp_version` 设置为 `"1.1.0"`；否则，`"1.0.0"` 仍然是正确的，并且是便携性首选。

v1.1 后端必须接受 `oamp_version` 为 `"1.0.0"`
或 `"1.1.0"` 的文档。v1.0 后端必须拒绝包含
v1.1 专用字段的 `"1.1.0"` 文档（根据 v1.0 §10.2 — 主要版本
兼容性规则）；然而，由于 v1.1 不引入新的顶级
必需字段，v1.0 后端应接受仅包含 v1.0 字段的 `"1.1.0"` 文档，忽略版本标签。

---

## 2. 能力发现

v1.1 引入一个新的端点，允许客户端发现后端支持哪些
OPTIONAL 功能。

### 2.1 GET `/v1/capabilities`

返回一个 JSON 对象，描述后端的协议表面。

**响应：**

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
      "description": "tenant:node 组合 (例如 '1:user')",
      "pattern": "^[0-9]+:.+$"
    },
    "id_preservation": "preserved",
    "content_types": ["application/json", "application/protobuf"],
    "auth_schemes": ["bearer"]
  }
}
```

**要求：**

- 宣传 v1.1 的后端必须实现此端点。
- 所有 `capabilities.*.supported` 字段必须是布尔值。
- 客户端应在每个连接生命周期中最多调用一次此端点，并
  缓存结果。
- 后端可以在 `capabilities.metadata`（对象）下包含供应商特定的键。客户端必须容忍未知键。

**`user_id_format`（必需）：**

后端必须宣传其 `user_id` 编码格式，以便跨多个 OAMP 后端的客户端
可以在尝试跨后端导入/导出之前进行兼容性预检查。该对象包含：

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `description` | string | MUST | 格式的可读描述（例如，`"tenant:node 组合 (例如 '1:user')"`，`"64 字符小写十六进制 Ed25519 公钥"`）。 |
| `pattern` | string | MAY | 匹配此后端有效 `user_id` 值的 ECMA-262 正则表达式。客户端可以用于预验证。 |

OAMP 文档中的 `user_id` 字段仍然是一个不透明字符串（模式中没有格式约束）。能力广告仅用于客户端兼容性检查。跨后端传输时，具有不兼容 `user_id` 格式的客户端必须转换 `user_id` 值（这是客户端的责任，而不是后端的责任）。

**`id_preservation`（必需）：**

一个字符串，指示后端在 `POST /v1/import` 期间是否保留客户端提供的条目 ID。可以是：

- `"preserved"` -- 后端存储并返回客户端提供的 `id`
  不变。导入响应中的 `id_mappings` 字段将始终为空 `{}`。
- `"regenerated"` -- 后端可以为导入的条目分配新 ID
  （例如，从内部键的确定性派生）。导入响应中的 `id_mappings`
  字段必须包含从每个原始 ID 到其新分配 ID 的映射。

跨多个 OAMP 后端并将条目 ID 用作连接键的客户端
必须检查 `id_preservation`，如果为 `"regenerated"`，则应用导入响应中的 `id_mappings`
以维护引用完整性。

### 2.2 v1.0 向后兼容性

v1.0 后端将对 `/v1/capabilities` 返回 `404 Not Found`。客户端
必须将此响应视为“后端为 v1.0；没有可用的 OPTIONAL 功能”
并回退到仅 REST 的行为。v1.0 后端也不宣传 `user_id_format` 或 `id_preservation`；跨多个
后端的客户端必须优雅地处理此情况（见 §5）。

### 2.3 导入响应形状（对 v1.0 §6.4 的澄清）

v1.0 §6.4 定义 `POST /v1/import` 返回 "`200 OK` 及摘要"
但未固定状态码或响应体形状。v1.1 强制执行以下内容：

**状态码：** `201 Created`。（客户端也必须接受来自 v1.0 后端的 `200 OK` 以实现向后兼容。）

**响应体：**

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

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `imported` | integer | MUST | 成功导入的条目数量。 |
| `skipped` | integer | MUST | 被跳过的条目数量（例如，重复且具有相等或更高置信度）。 |
| `rejected` | integer | MUST | 由于验证错误而被拒绝的条目数量。 |
| `id_mappings` | object | MUST | 原始 ID 到分配 ID 的映射。如果所有 ID 都被保留，则为空 `{}`。见 §2.4。 |
| `rejections` | array | MAY | 被拒绝条目的详细信息。每个元素：`{"id": "...", "reason": "..."}`。 |

### 2.4 导入时条目 ID 保留（对 v1.0 §4.4 的澄清）

实现可以在导入期间保留或重新生成条目 ID，但
必须通过导入响应传达结果：

- **保留 ID 的后端**（在能力中宣传为 `id_preservation: "preserved"`）：存储客户端提供的 `id` 不变。导入响应中的 `id_mappings`
  字段必须为 `{}`。
- **重新生成 ID 的后端**（在能力中宣传为 `id_preservation: "regenerated"`）：在导入期间分配新 ID（例如，通过确定性派生）。导入响应中的 `id_mappings` 字段必须将每个导入条目的原始 ID 映射到其新分配的 ID。

这使得两种架构模式都能兼容，而无需更改其内部设计。依赖 ID 稳定性的客户端（例如，基于条目 ID 构建内存图的代理）必须检查 `id_mappings` 并在导入后更新其引用。

---

## 3. 流式传输 (OPTIONAL)

### 3.1 动机

OAMP v1.0 是基于轮询的：客户端通过重新发出
搜索查询来了解内存变化。对于交互式代理、可观察性表面和仪表板，这会产生高轮询负载或过时的 UI。v1.1 定义了一个 WebSocket
子协议，允许客户端在内存变更发生时进行订阅。

这是 OPTIONAL，因为 (a) 并非每个后端都有实时事件源，
以及 (b) v1.0 中的轮询模型仍然是正确且足够的，适用于批处理代理。

### 3.2 端点

支持流式传输的 v1.1 后端必须公开：

- **URL：** `wss://{host}/v1/stream`（或用于非 TLS 开发的 `ws://`）
- **子协议：** `oamp.v1`（通过标准 WebSocket
  `Sec-WebSocket-Protocol` 头进行协商）

如果客户端未在子协议列表中请求 `oamp.v1`，后端必须拒绝升级并返回 HTTP `400 Bad Request`。

### 3.3 认证

WebSocket 升级必须以与 REST API 相同的方式进行身份验证。后端
应在升级请求中通过 `Authorization` 头接受 bearer token，并且可以接受作为浏览器客户端无法在 WebSocket 升级中设置头的 `?token=` 查询参数。所选方案必须在 `/v1/capabilities` 中声明。

### 3.4 帧格式

所有帧都是 **文本帧**，携带单个 JSON 对象。（二进制帧
保留用于未来的 protobuf 模式流式传输，且在 v1.1 中不得使用。）

每个帧的形状为：

```json
{
  "oamp_version": "1.1.0",
  "type": "<frame_type>",
  "id": "<uuid_v4>",
  "ts": "<iso8601>",
  "payload": { ... }
}
```

`id` 是客户端用于关联回复的每帧标识符；`ts`
是帧发出时后端的单调时间戳。

### 3.5 客户端 → 服务器帧

| `type`         | 目的                                            |
|----------------|----------------------------------------------------|
| `subscribe`    | 打开带有过滤器的订阅。                          |
| `unsubscribe`  | 关闭先前打开的订阅。                            |
| `ping`         | 存活探测；后端必须以 `pong` 响应。              |

**`subscribe` 负载：**

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

- `subscription_id` 是客户端选择的，必须在每个连接中唯一。服务器在每个后续事件和取消订阅确认中使用它。
- `user_id` 是必需的。后端必须拒绝跨用户订阅
  （返回带有代码 `"forbidden"` 的 `error` 帧）。
- `event_types` 可以省略，以订阅后端支持的所有事件类型。
- `filters` 是可选的；已识别的过滤器键在 §3.7 中列出。未知
  过滤器键必须被忽略，而不是被拒绝。
- `include_initial_snapshot`（默认 `false`）：如果为 `true`，后端必须
  发出一个 `knowledge_snapshot` 帧，包含当前匹配状态
  在任何实时事件流动之前。

### 3.6 服务器 → 客户端帧

| `type`                | 目的                                              |
|-----------------------|------------------------------------------------------|
| `subscribed`          | 确认订阅。                                          |
| `unsubscribed`        | 确认取消订阅。                                     |
| `knowledge_created`   | 存储了一个新的 `KnowledgeEntry`。                   |
| `knowledge_updated`   | 修改了一个现有的 `KnowledgeEntry`（PATCH）。       |
| `knowledge_deleted`   | 一个 `KnowledgeEntry` 被永久删除。                  |
| `knowledge_snapshot`  | 针对 `include_initial_snapshot` 的一次性快照。      |
| `user_model_updated`  | 更新了一个 `UserModel` 行。                         |
| `error`               | 协议或应用错误。                                   |
| `pong`                | 存活回复。                                          |

**`knowledge_created` 负载：**

```json
{
  "subscription_id": "<echoed-from-subscribe>",
  "entry": { /* 完整的 v1.0 KnowledgeEntry 文档 */ }
}
```

`knowledge_updated` 携带 **更新后的** 条目。`knowledge_deleted`
仅携带 `{ "subscription_id": "...", "id": "<uuid>", "user_id": "..." }`
以满足 v1.0 “日志中无内容” 规则，即使在传输中 — 被删除的内容不得重新广播。

**`error` 负载：**

```json
{
  "subscription_id": "<id-or-null>",
  "code": "forbidden | invalid | rate_limited | internal",
  "message": "可读的",
  "retryable": false
}
```

### 3.7 识别的过滤器键

| 键        | 类型            | 语义                                  |
|------------|-----------------|--------------------------------------------|
| `category` | 字符串数组      | 匹配这些 v1.0 类别中的任何一个。        |
| `tags`     | 字符串数组      | 条目必须包含至少一个列出的标签。        |
| `min_confidence` | 数字      | 条目的 `confidence` 必须 ≥ 此值。 |

后端可以支持额外的过滤器键；它们必须在
`/v1/capabilities.streaming.filter_keys` 中进行宣传。

### 3.8 背压与交付

- 该协议是 **至多一次**。如果客户端无法跟上，后端
  可以丢弃事件，并应发出一个带有代码
  `"rate_limited"` 和 `retryable: true` 的单个 `error` 帧以信号缺口。需要
  精确一次语义的客户端必须通过 `/v1/knowledge` 轮询进行调和。
- 后端必须在 60 秒内没有客户端流量后关闭 WebSocket
  （没有 `ping`，没有其他帧）。客户端应每 30 秒发送一次 `ping`。
- 后端必须容忍每个连接至少 16 个并发订阅。

### 3.9 隐私

v1.0 §8 隐私规则适用于流式内容，就像它是 REST
响应一样：

- 知识内容不得在连接的任一方记录。
- `knowledge_deleted` 帧不得包含被删除的内容。
- 订阅必须限制在单个 `user_id`。多用户分发是 v2.0 的问题。

---

## 4. 双时间 `as_of` 查询参数 (OPTIONAL)

### 4.1 动机

许多内存后端（cosmictron, kizuna-mem 等）已经存储
双时间数据 — 一个 `valid_time` 轴（事实在世界上何时为真）
和一个 `ingest_time` 轴（系统何时学习到事实）。v1.0 没有
询问“在时间 T 时你知道什么？”的方式，这在以下情况下是必要的：

- 代理决策的重放和调试。
- 合规审计（“在做出此决策时文件中有什么？”）。
- 可观察性仪表板中的反向时间旅行 UI。

v1.1 定义了一个单一的、普遍适用的查询参数，暴露
此存储能力，而不规定内部表示。

### 4.2 参数

支持 `as_of` 的后端必须在以下列出的端点上接受以下查询参数：

```
?as_of=<iso8601-datetime>
```

受影响的端点：

| 端点                              | 带 `as_of` 的语义                          |
|-----------------------------------|-------------------------------------------------|
| `GET /v1/knowledge?query=...`     | 搜索在 `as_of` 时存在的索引。                  |
| `GET /v1/knowledge/{id}`          | 返回在 `as_of` 时条目的状态。                 |
| `GET /v1/user-model/{user_id}`    | 返回在 `as_of` 时的用户模型。                 |

变更端点（`POST`、`PATCH`、`DELETE`）不得接受 `as_of`
并且如果提供该参数必须响应 `400 Bad Request`。

### 4.3 语义

可能有两个语义轴。后端必须默认选择 **ingest_time 语义**：
“向我展示如果在 `as_of` 时发出此相同查询将返回的结果。”这是唯一普遍定义良好的
解释，也是所有已知参考后端实现的内容。

如果后端支持 `valid_time` 查询（世界状态轴），它必须通过一个单独的、明确命名的参数（例如，
`?valid_at=`）来公开它。v1.1 为此目的保留 `valid_at`，但不对其进行标准化；这属于 v2.0 的工作。

### 4.4 响应形状

响应体必须与等效的 v1.0 响应完全相同。v1.1
仅更改主体描述的历史状态。

一个支持 v1.1 的后端应包括响应头
`OAMP-As-Of: <iso8601>`，回显它使用的时间戳。客户端可以使用
此信息来检测时间戳规范化（例如，后端四舍五入到其
存储分辨率）。

### 4.5 超范围时间戳

- 未来的 `as_of` 必须视为 `now`。后端应
  将 `OAMP-As-Of` 设置为实际解析的时间戳。
- 在用户的第一次摄取事件之前的 `as_of` 必须返回一个空
  结果集（HTTP 200），而不是 404。
- 后端由于保留/快照过期而无法解析的 `as_of` 必须返回 `409 Conflict`，并带有 `code: "as_of_expired"`。

### 4.6 能力广告

`/v1/capabilities.as_of.min_resolution_ms` 必须报告后端可以解析的最小时间
增量（例如，快照间隔）。客户端不应假设亚毫秒分辨率。

---

## 5. 合规性

声称 **v1.1 合规** 的后端必须：

1. 满足每个 v1.0 强制要求。
2. 实现 `GET /v1/capabilities` 返回真实的能力标志。
3. 对于每个它宣传的 OPTIONAL 功能（`streaming`、`as_of`）：
   实现第 §3 或 §4 中描述的完整表面。
4. 使用文档中的 HTTP/WebSocket 错误代码拒绝不支持的 OPTIONAL 功能；绝不默默忽略。

后端可以声称 v1.1 合规，**不支持任何 OPTIONAL 功能**。这很有用：它向客户端发出信号，表明后端
理解 v1.1 词汇，并将在 `/v1/capabilities` 中公开未来的 OPTIONAL 功能，而不是作为不可发现的扩展。

位于 `/validators/validate.sh` 的验证器将在单独的 PR 中获得 v1.1 夹具；v1.1 文档必须针对未更改的 v1.0 JSON 模式进行验证。

---

## 6. v1.0 客户端的迁移路径

与 v1.1 后端通信的 v1.0 客户端继续正常工作，无需更改。
希望选择 v1.1 功能的 v1.0 客户端：

1. 发出 `GET /v1/capabilities` 并检查响应。
2. 如果 `streaming.supported`，打开 WebSocket 并遵循 §3。
3. 如果 `as_of.supported`，在有用的读取请求中附加 `?as_of=`。

在存储的文档中无需提升 `oamp_version`。版本
字符串描述的是文档，而不是会话 — v1.1 客户端可以很好地存储 v1.0
文档。

---

## 7. v1.1 最终确定的开放问题

这些问题在 v1.1 标记为稳定之前将进行社区讨论：

1. **跨重连的订阅恢复。** 客户端是否应该能够在 `subscribe` 时传递 `since=<event_id>` 以重播错过的事件？
   这要求后端保留事件日志；许多后端并不这样做。*暂定答案：* 留给 v2.0。
2. **快照分页。** 对于一个有 100k 条目的用户，今天的 `knowledge_snapshot` 帧是一个单帧。我们是否应该强制分块？
   *暂定答案：* 如果后端报告 `streaming.snapshot_max_entries` 限制，则强制 `snapshot_chunk`；否则单帧。
3. **`valid_at` 标准化。** 来自金融和合规的真实需求表明，`valid_at` 对某些工作流比 `as_of` 更有用。
   *暂定答案：* 在 v1.1 中落地 `as_of`，将 `valid_at` 保留到 v1.2 或 v2.0，一旦 ≥2 个后端发布可互操作的实现。
4. **gRPC 流式传输。** 流式子协议是否应该有 gRPC 绑定？*暂定答案：* `/proto/` 目录将在 JSON 形状稳定后获得 `service Stream { rpc Subscribe(stream SubscribeRequest) returns (stream Event); }`。

---

## 附录 A：能力模式

`/v1/capabilities` 响应的 JSON 模式将在
`spec/v1.1/capabilities.schema.json` 中添加，一旦 §2 最终确定。第 §2.1 中的形状是工作定义。

## 附录 B：参考实现目标

两个参考后端将在此草案发布时同时实现 v1.1 OPTIONAL 功能：

- **cosmictron** (Rust) — `/v1/capabilities`、`/v1/oamp/*` REST、
  `/v1/oamp/stream` WebSocket 子协议、内存读取中的 `?as_of=`。见
  `cosmictron/docs/design/OAMP_TRANSPORT.md`。
- **kizuna-mem** (Zig 核心 + Rust 边车) — 相同表面；WebSocket
  从 Rust 边车提供。见
  `kizuna-dream/docs/design/OAMP_TRANSPORT.md` 和
  `kizuna-dream/docs/design/WEBSOCKET_EVENT_STREAM.md`。

这些实现是对规范的合规性压力测试；如果
其中任何一个无法顺利落地此草案，则在 v1.1 最终确定之前将对草案进行修订。