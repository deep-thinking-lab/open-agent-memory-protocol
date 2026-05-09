# 开放代理内存协议 — v1.2 受管内存

**状态：** 稳定  
**日期：** 2026-05-09  
**作者：** Jonathan Conway (Deep Thinking)  
**相关实现：** `cosmictron`, `kizuna-mem`, `ultra`, `toraeru`  
**依赖于：** `spec/v1/oamp-v1.md`, `spec/v1.1/oamp-v1.1.md`

---

## 1. 为什么存在这个协议

多个 OAMP 后端现在需要一流的受管内存：

- **kizuna-mem** 需要企业级敏感性类别、关注来源的政策评估和结构化的保留原因。
- **cosmictron** 需要对政策范围内的内存和导出/导入的治理元数据进行互操作处理。
- **ultra** 将消费和生成受管内存，因此如果我们希望后端可移植，特定于供应商的 `metadata.*` 数据块已不再足够。
- **toraeru** 将与 OAMP 集成，并需要相同的可移植元数据合同，而不是特定于后端的治理负载。

目前，OAMP v1.0/v1.1 只能将受管内存数据作为供应商扩展放在 `metadata` 中，这符合规范。然而：

1. 没有治理元数据的标准形状，
2. 没有受管内存的标准能力广告，
3. 没有更丰富的多源来源的可移植表示，
4. 没有“保留”或“编辑过的存根”的标准线级概念。

该提案将前面三项标准化为 **附加的 v1.2 工作**，并明确将第四项推迟到 **v2.0**，因为当前的 v1.x 架构和流负载规则不允许在不进行破坏性更改的情况下实现可移植的编辑过的存根。

---

## 2. 推荐摘要

### 在 v1.2 中标准化

- `KnowledgeEntry` 上的可选 `governance` 对象
- `KnowledgeEntry` 上的可选 `provenance` 扩展对象
- `GET /v1/capabilities` 广告以支持治理
- 可选的治理感知过滤键用于搜索/流
- 受管内存字段和往返容忍度的合规性测试

### 推迟到 v2.0

- 标准化的编辑/保留结果文档
- 可以混合可见条目和保留存根的标准化 REST 响应形状
- 标准化的流事件类型用于保留知识

---

## 3. 为什么保留存根不是 v1.2 的更改

该提案故意不在 v1.2 中标准化保留存根。

原因：

1. 在 v1.0 中，`KnowledgeEntry.content` 是必需的，并且 MUST 是一个非空字符串。
2. 搜索/列表响应是围绕 `KnowledgeEntry` 对象的数组定义的。
3. v1.1 流式传输表示 `knowledge_created` 和 `knowledge_updated` 携带完整的 `KnowledgeEntry`。

这意味着一个可移植的“存根”如下：

```json
{
  "type": "knowledge_entry",
  "content": null,
  "withheld": true
}
```

在当前的 v1.x 架构术语中是无效的。使 `content` 可选或可为空将是一个破坏性架构更改，而不是附加的。

因此，正确的标准分割是：

- **v1.2：** 标准化治理元数据和发现
- **v2.0：** 标准化保留结果语义

后端 MAY 继续在其自己的扩展中实现特定于供应商的保留行为，直到 v2.0 设计落地。

---

## 4. 提议的 v1.2 增加

## 4.1 `KnowledgeEntry` 上的可选 `governance` 字段

添加一个新的可选顶级字段：

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

### 提议的字段形状

| 字段 | 类型 | 要求 | 描述 |
|------|------|------|------|
| `governance` | 对象 | MAY | 标准受管内存元数据 |
| `governance.sensitivity_class` | 字符串 | 如果 `governance` 存在则 MUST | 之一 `public`, `internal`, `confidential`, `restricted` |
| `governance.labels` | 字符串数组 | MAY | 后端或租户定义的治理标签 |
| `governance.handling` | 对象 | MAY | 表面特定的治理提示 |
| `governance.handling.retrieval` | 字符串 | MAY | `governed` 或 `ungoverned` |
| `governance.handling.export` | 字符串 | MAY | `governed` 或 `ungoverned` |
| `governance.handling.stream` | 字符串 | MAY | `governed` 或 `ungoverned` |

### 注意事项

- 此字段是 **描述性的**，而不是完整的政策语言。
- 它告诉其他后端和代理知识是如何分类的。
- 它并不标准化访问控制评估规则。
- 后端 MAY 将更丰富的本地政策结构映射到 `metadata` 中，除了标准的 `governance` 字段。

## 4.2 `KnowledgeEntry` 上的可选扩展 `provenance` 字段

保持 `source` 完全不变，并添加一个可选的更丰富的来源结构：

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

### 提议的字段形状

| 字段 | 类型 | 要求 | 描述 |
|------|------|------|------|
| `provenance` | 对象 | MAY | 扩展的来源元数据 |
| `provenance.sources` | 数组 | 如果 `provenance` 存在则 MUST | 有序的证据/来源列表 |
| `provenance.sources[].session_id` | 字符串 | MUST | 来源会话标识符 |
| `provenance.sources[].timestamp` | 字符串 | MUST | ISO 8601 获取时间 |
| `provenance.sources[].agent_id` | 字符串 | MAY | 来源代理标识符 |
| `provenance.sources[].turn_id` | 字符串 | MAY | 回合/消息本地标识符 |
| `provenance.derived` | 布尔值 | MAY | 此条目是否是从多个来源合成的 |

### 注意事项

- `source` 仍然是强制性的，并且仍然是最小的来源合同。
- `provenance` 是更丰富的互操作来源扩展，适用于支持合并、合成或证据链的后端。

## 4.3 治理能力广告

在 `/v1/capabilities.capabilities` 下添加一个可选的 `governance` 对象：

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

### 提议的字段

| 字段 | 类型 | 要求 | 描述 |
|------|------|------|------|
| `governance.supported` | 布尔值 | 如果 `governance` 存在则 MUST | 后端理解标准化的治理字段 |
| `governance.sensitivity_classes` | 字符串数组 | MUST | 后端接受的类别 |
| `governance.labels_supported` | 布尔值 | MUST | 是否存储/保留自由形式的治理标签 |
| `governance.extended_provenance_supported` | 布尔值 | MUST | 是否存储/保留 `provenance` |
| `governance.withheld_stub_support` | 布尔值 | MUST | 后端是否具有任何非标准的保留存根行为 |

`withheld_stub_support` 在 v1.2 中仅为信息性。它并不意味着有标准化的线格式。

## 4.4 可选的治理感知过滤器

在后端支持过滤广告的情况下，标准化这些可选键：

| 键 | 类型 | 语义 |
|----|------|-------|
| `sensitivity_class` | 字符串数组 | 匹配 `governance.sensitivity_class` 在集合中的条目 |
| `governance_label` | 字符串数组 | 匹配至少包含一个列出的治理标签的条目 |

这适用于：

- REST 搜索，后端特定查询模型支持时
- `streaming.filter_keys`，当支持流时

这些键是可选的，因为并非每个后端都索引治理元数据。

---

## 5. 架构和 OpenAPI 影响

该提案需要一个新的次要版本架构，因为当前的 v1.0 JSON 架构在 `KnowledgeEntry` 和 `KnowledgeStore` 条目项上设置了 `additionalProperties: false`。

因此，v1.2 工作必须包括：

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

带有附加的可选字段：

- `governance`
- `provenance`

在 v1.2 中没有必需字段的更改。

---

## 6. 兼容性规则

### v1.2 后端行为

- MUST 接受 v1.0 和 v1.1 文档。
- MUST 在提供时保留 `governance` 和 `provenance`，除非文档政策或存储限制明确拒绝它们。
- MUST 像以前一样忽略未知的额外供应商元数据。

### v1.0 / v1.1 客户端行为

- v1.0 或 v1.1 客户端可以忽略 `governance` 和 `provenance`，如果它不理解它们。
- 这是安全的，因为两者都是可选的附加字段。

### 导入/导出期望

- 支持治理的后端 SHOULD 在导出/导入时保留标准化的治理字段。
- 不支持治理的后端 SHOULD 仍然接受文档，并将字段保留为不透明数据或记录它们被丢弃。

---

## 7. v1.2 的非目标

以下内容明确不在本提案的范围内：

- 标准化的允许/拒绝政策语言
- 跨后端授权语义
- 标准化的 `withholding_reason`
- 标准化的编辑过的 `KnowledgeEntry` 存根形状
- 多用户订阅语义

这些需要：

- 单独的 v2.0 设计，或
- 一个新的非 `KnowledgeEntry` 响应/事件封装，不符合当前 v1.x 的预期。

---

## 8. 合规性增加

如果 v1.2 成立，添加合规案例：

- `POST /v1/knowledge` 接受 `governance`
- `POST /v1/knowledge` 接受 `provenance`
- `GET /v1/knowledge/:id` 往返标准化治理字段
- `POST /v1/import` 在支持的情况下保留治理/来源
- `/v1/capabilities` 准确广告治理支持

在 v1.2 中 **不** 添加保留存根合规性测试。

---

## 9. 提议的上游问题分解

### 问题 1：批准受管内存范围分割

决定并记录：

- v1.2 标准化治理元数据 + 发现
- v2.0 处理保留/编辑结果语义

### 问题 2：将 `governance` 和 `provenance` 添加到 v1.2 架构

文件：

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`
- 参考类型库

### 问题 3：能力广告和过滤键

文件：

- `spec/v1.2/oamp-v1.2.md`
- `spec/v1.2/openapi.yaml`
- 如果重用或取代，则为 v1.1 能力文本

### 问题 4：合规性套件覆盖

文件：

- `reference/compliance/README.md`
- `reference/compliance/src/oamp_compliance/tests/`

### 问题 5：参考后端支持

文件：

- `reference/server/`
- 语言参考类型

### 问题 6：v2.0 RFC 用于保留结果

为以下内容打开一个单独的设计轨道：

- 非破坏性封装选项与主要版本架构更改
- 针对政策保留的 REST 语义
- 针对保留更新的流语义
- `withholding_reason` 的可移植性

---

## 10. 推荐

采用该提案作为工作方向：

1. 在 v1.2 中标准化受管内存元数据，
2. 在 v1.2 中标准化更丰富的来源，
3. 将保留/编辑语义排除在 v1.2 之外，
4. 为可移植的保留结果打开一个单独的 v2.0 RFC。

这为 `cosmictron`、`kizuna-mem`、`ultra` 和 `toraeru` 提供了一个共同的互操作目标，而不假装当前的 v1.x `KnowledgeEntry` 形状已经能够表达我们想要的每种受管内存行为。