# 开放代理内存协议 — 版本 1.2.0

**状态：** 稳定  
**日期：** 2026-05-09  
**作者：** Jonathan Conway (Deep Thinking)  
**替代：** 无 — 以附加方式扩展 v1.0.0 和 v1.1.0  
**仓库：** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 摘要

OAMP v1.2 是 v1.0.0 和可选 v1.1 草案功能的 **严格附加** 小版本。它为以下内容标准化了可移植的结构：

- `KnowledgeEntry` 上的受管内存元数据，
- `KnowledgeEntry` 上更丰富的多源来源，
- `GET /v1/capabilities` 上的治理能力广告，以及
- 用于搜索和流媒体表面的治理感知过滤键。

v1.2 故意 **不** 标准化保留或编辑过的结果文档。这些语义需要新的响应信封或对 `KnowledgeEntry` 合同的重大更改，因此它们被明确推迟到单独的 v2.0 设计轨道。

本文档中的关键字 "MUST"、"MUST NOT"、"REQUIRED"、"SHALL"、"SHALL NOT"、"SHOULD"、"SHOULD NOT"、"RECOMMENDED"、"MAY" 和 "OPTIONAL" 应按 [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) 中描述的方式进行解释。

---

## 1. 与 v1.0 和 v1.1 的关系

v1.2 重用所有 v1.0 架构、端点、要求和语义，以及可选的 v1.1 能力模型，而不更改任何必需字段。

唯一的新传输级别添加是：

- OPTIONAL `governance` 在 `KnowledgeEntry` 上
- OPTIONAL `provenance` 在 `KnowledgeEntry` 上
- OPTIONAL `capabilities.governance` 在 `GET /v1/capabilities` 上
- OPTIONAL 治理感知过滤键

文档在使用 v1.2 专用字段时 SHOULD 将 `oamp_version` 设置为 `"1.2.0"`。仅使用 v1.0 字段的文档 MAY 继续使用 `"1.0.0"` 以实现最大可移植性。

---

## 2. 范围划分

### 2.1 在 v1.2 中标准化

- 可移植的受管内存元数据
- 可移植的更丰富来源
- 受管内存支持的能力发现
- 可选的治理感知过滤

### 2.2 明确推迟到 v2.0

- 标准化的保留或编辑过的结果文档
- 包含可见条目和保留存根的混合结果集
- 用于保留知识的流事件有效负载
- 可移植的 `withholding_reason` 语义
- 标准化的跨后端授权政策语言

此划分对 v1.2 草案是规范性的。实现 MUST NOT 声称保留或编辑过的存根由 v1.2 标准化。

---

## 3. `KnowledgeEntry` 添加

### 3.1 可选的 `governance`

`KnowledgeEntry` 增加了一个 OPTIONAL `governance` 对象：

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

#### 字段

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `governance` | object | MAY | 标准的受管内存元数据 |
| `governance.sensitivity_class` | string | MUST if `governance` present | 之一 `public`、`internal`、`confidential`、`restricted` |
| `governance.labels` | array of string | MAY | 后端或租户定义的治理标签 |
| `governance.handling` | object | MAY | 特定表面的处理提示 |
| `governance.handling.retrieval` | string | MAY | `governed` 或 `ungoverned` |
| `governance.handling.export` | string | MAY | `governed` 或 `ungoverned` |
| `governance.handling.stream` | string | MAY | `governed` 或 `ungoverned` |

`governance` 对象是描述性的。它不是一个可移植的政策引擎。

### 3.2 可选的 `provenance`

`KnowledgeEntry` 保留现有的 REQUIRED `source` 对象，并添加一个 OPTIONAL 更丰富的 `provenance` 对象：

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

#### 字段

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `provenance` | object | MAY | 扩展的血统元数据 |
| `provenance.sources` | array | MUST if `provenance` present | 有序证据/来源列表 |
| `provenance.sources[].session_id` | string | MUST | 来源会话标识符 |
| `provenance.sources[].timestamp` | string | MUST | ISO 8601 获取时间 |
| `provenance.sources[].agent_id` | string | MAY | 来源代理标识符 |
| `provenance.sources[].turn_id` | string | MAY | 回合/消息本地标识符 |
| `provenance.derived` | boolean | MAY | 此条目是否是从多个来源合成的 |

现有的 `source` 字段仍然是最小的来源合同，且 MUST 仍然存在。

---

## 4. 能力添加

v1.2 扩展了 v1.1 `GET /v1/capabilities` 响应，增加了一个 OPTIONAL `capabilities.governance` 对象：

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

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `governance.supported` | boolean | MUST if `governance` present | 后端理解标准化的治理字段 |
| `governance.sensitivity_classes` | array of string | MUST | 后端接受的类别 |
| `governance.labels_supported` | boolean | MUST | 是否存储和保留自由格式标签 |
| `governance.extended_provenance_supported` | boolean | MUST | 是否存储和保留 `provenance` |
| `governance.withheld_stub_support` | boolean | MUST | 后端是否具有任何非标准的保留行为 |

`withheld_stub_support` 在 v1.2 中仅为信息性，且 MUST NOT 被视为可移植结果格式保证。

---

## 5. 治理感知过滤键

已经支持查询过滤器或流订阅过滤器的后端 MAY 广告并接受这些 OPTIONAL 治理感知键：

| 键 | 类型 | 语义 |
|-----|------|-----------|
| `sensitivity_class` | array of string | 匹配 `governance.sensitivity_class` 在集合中的条目 |
| `governance_label` | array of string | 匹配至少包含一个列出的治理标签的条目 |

对于 REST 搜索端点，这些 MAY 作为重复的查询参数出现。对于流媒体，这些 MAY 出现在 `streaming.filter_keys` 广告和订阅有效负载中。

不索引治理元数据的后端 MAY 拒绝或忽略这些键，但 MUST 准确地在能力中广告支持。

---

## 6. 兼容性规则

### 6.1 v1.2 后端

- MUST 接受 v1.0 和 v1.1 文档。
- MUST 在支持时保留 `governance` 和 `provenance`。
- MUST 继续容忍未知的供应商特定元数据扩展。

### 6.2 v1.0 和 v1.1 客户端

- MAY 如果不理解 `governance` 和 `provenance` 则忽略它们。
- MUST NOT 仅根据 v1.2 版本字符串假设保留或编辑过的结果语义。

### 6.3 导入和导出

- 支持受管内存的后端 SHOULD 在导出和导入时保留标准化的 `governance` 和 `provenance`。
- 不支持受管内存的后端 SHOULD 记录这些字段是以不透明方式保留还是被丢弃。

---

## 7. 架构和 OpenAPI 工件

v1.2 草案由以下内容表示：

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

这些工件是对 `spec/v1/` 的附加，并且不更改 v1.0 必需字段合同。