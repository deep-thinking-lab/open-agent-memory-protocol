# 开放代理内存协议 — 版本 1.3.0（草案）

**状态：** 草案（提议的小版本）  
**日期：** 2026-05-07  
**作者：** Jonathan Conway（深度思考）  
**取代：** 无 — 以附加方式扩展 v1.0.0、v1.1.0 和 v1.2.0  
**仓库：** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 摘要

OAMP v1.3 是 v1.0.0 及可选的 v1.1 和 v1.2 草案功能的 **严格附加** 小版本。它标准化了在 v1.2 中描述性引入的受管内存的 **执行** 层。

v1.2 标准化了：

- `governance.sensitivity_class`
- `governance.labels`
- `governance.handling`
- 更丰富的 `provenance`
- 治理能力发现

v1.3 定义了当多个代理为同一用户访问同一后端时，后端必须对这些字段执行的操作。它标准化了：

- 可移植的代理授权声明
- 层次标签匹配约定
- 读取、写入、导入、导出和流过滤规则
- 代理表面上的存在隐藏
- 代理身份与来源的绑定
- 审计日志的添加
- 执行支持的能力广告

v1.3 仍然是 **基于省略** 的。它 **不** 标准化可移植的保留或编辑结果文档。该工作将推迟到单独的 v2.0 路径。

本文档中的关键字 "MUST"、"MUST NOT"、"REQUIRED"、"SHALL"、"SHALL NOT"、"SHOULD"、"SHOULD NOT"、"RECOMMENDED"、"MAY" 和 "OPTIONAL" 应按 [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) 中的描述进行解释。

---

## 1. 与早期版本的关系

v1.3 重用每个 v1.0 架构、端点、要求和语义规则，以及可选的 v1.1 能力模型和附加的 v1.2 受管内存元数据模型。

v1.3 中唯一的新传输级别添加是：

- 可选的 `capabilities.governance.enforcement` 在 `GET /v1/capabilities` 上
- 用于 JWT 声明或 `OAMP-Grant` 的可移植代理授权声明格式
- 消耗现有 v1.2 `governance` 字段的规范后端行为

v1.3 引入 **没有新的 `KnowledgeEntry` 字段** 和 **没有新的 `KnowledgeStore` 字段**。

仅使用 v1.0-v1.2 条目/存储字段的文档可以继续使用 `"1.2.0"` 作为 `oamp_version`。希望宣传 v1.3 草案线的文档和响应可以使用 `"1.3.0"`。

---

## 2. 范围划分

### 2.1 在 v1.3 中标准化

- 可移植的每代理授权声明
- 层次治理标签执行语义
- v1.2 治理处理提示的操作意义
- 读取过滤
- 写入拒绝
- 导入拒绝会计
- 导出过滤和 `oamp_export_full`
- 在 v1.1 表面上的流过滤
- 代理表面上的存在隐藏
- 与 `oamp_agent_id` 的来源绑定
- 治理执行能力广告
- 授权和范围事件的审计操作名称

### 2.2 明确推迟到 v2.0

- 标准化的保留或编辑结果文档
- 包含可见条目和保留存根的混合结果集
- 可移植的 `withholding_reason` 语义
- 明确表示保留知识的流负载
- 可移植的跨后端授权政策语言

实现必须不声称 v1.3 标准化保留或编辑的存根文档。

---

## 3. v1.2 治理元数据的操作重用

v1.3 添加 **没有新的条目级治理字段**。相反，它使 v1.2 字段具有操作性。

### 3.1 `governance.sensitivity_class`

v1.2 枚举的顺序为：

`public < internal < confidential < restricted`

代理授权携带 `oamp_sensitivity_max`。有效的 `sensitivity_class` 超过授权上限的条目将被过滤或拒绝。

当 `governance` 缺失时，出于执行目的，有效类别为 `internal`。

### 3.2 `governance.labels`

v1.3 引入了由执行使用的层次标签约定。

- 标签应为匹配 `^[a-z][a-z0-9]*(\\.[a-z][a-z0-9_]*)*$` 的点分小写 ASCII 路径
- 应用层次前缀匹配
- 对于 `health` 的授权匹配 `health.condition` 和 `health.condition.diagnosis`

跨供应商互操作性的保留顶级标签：

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

特定于供应商的扩展应位于 `x.<vendor>.<...>` 下。

不符合层次约定的标签仍然是有效的描述性 v1.2 标签，但执行 v1.3 的后端应将其视为不透明的精确匹配值。

当 `governance.labels` 缺失或为空时，有效标签集为 `["behaviour"]`，用于执行目的。

### 3.3 `governance.handling`

v1.2 的 `handling` 提示在 v1.3 中变得重要：

- `retrieval: "governed"` 意味着读取路径必须应用授权过滤
- `retrieval: "ungoverned"` 使条目免于读取路径过滤
- `export: "governed"` 意味着导出路径必须应用授权过滤
- `export: "ungoverned"` 使条目免于导出路径过滤
- `stream: "governed"` 意味着 v1.1 流路径必须应用授权过滤
- `stream: "ungoverned"` 使条目免于流过滤
- `mediation: "required"` 意味着访问条目需要来自受信任的中介发行者的有效授权
- `mediation: "optional"` 意味着没有表达中介约束

当 `governance` 存在且省略了处理值时，该表面的有效默认值为 `governed`。

当省略 `mediation` 时，有效默认值为 `optional`。

---

## 4. 代理授权声明

### 4.1 JWT 声明形状

当承载身份验证使用 JWT 时，令牌携带以下附加声明：

```json
{
  "iss": "governor",
  "sub": "user-abc",
  "oamp_agent_id": "medical-assistant-v3",
  "oamp_grant_id": "grant-2026-05-07-001",
  "oamp_read_labels": ["health", "preferences"],
  "oamp_write_labels": ["health", "preferences"],
  "oamp_sensitivity_max": "restricted",
  "oamp_export_full": false,
  "oamp_mediation_required": true,
  "oamp_task_id": "task-7",
  "oamp_context_id": "mission-3",
  "exp": 1746662400
}
```

| 声明 | 要求 | 描述 |
|-------|-------------|-------------|
| `oamp_agent_id` | MUST | 调用代理的稳定标识符 |
| `oamp_grant_id` | MUST | 授权实例的稳定标识符 |
| `oamp_read_labels` | MUST | 代理可以读取的标签 |
| `oamp_write_labels` | MUST | 代理可以写入的标签 |
| `oamp_sensitivity_max` | MUST | 最高可读/可写的敏感性类别 |
| `oamp_export_full` | MAY | 是否授权完全未过滤的导出 |
| `iss` | 对于需要中介的资源必须 | 颁发授权的权威的稳定标识符 |
| `oamp_mediation_required` | MAY | 表示该授权旨在用于中介流 |
| `oamp_task_id` | MAY | 代理被配置执行的工作单元的标识符 |
| `oamp_context_id` | MAY | 任务上方的不透明分组标识符 |

空的 `oamp_read_labels` 意味着不读取任何内容。

### 4.2 `OAMP-Grant` 头

对于不使用 JWT 承载令牌的部署，相同的声明对象可以通过 `OAMP-Grant` 头传递。头部值必须是对声明对象的紧凑 JWS。

### 4.3 来源绑定

当在 v1.3 授权下发生写入时，后端必须验证：

- `entry.source.agent_id == oamp_agent_id`，当 `source.agent_id` 存在时

对于具有 `provenance.sources[*].agent_id` 的条目，后端应验证每个列出的 `agent_id` 是否与调用授权或其本地信任模型相符。

当在携带 `oamp_task_id` 或 `oamp_context_id` 的 v1.3.1 授权下发生写入时，后端应将这些值印章到由该授权生成的 `provenance.sources[*].task_id` 和 `provenance.sources[*].context_id` 上。这些字段仅为描述性归属，必须不扩大访问。

---

## 5. 后端执行规则

宣传 `governance.enforcement.supported: true` 的后端必须应用这些规则。

### 5.1 读取过滤

条目仅在以下情况下通过受管读取：

1. 有效的检索处理不被豁免，并且
2. 至少一个有效条目标签被某些授权读取标签匹配，并且
3. 有效的敏感性类别小于或等于 `oamp_sensitivity_max`

未通过的条目必须不出现在：

- `GET /v1/knowledge/{id}`
- `GET /v1/knowledge`
- 搜索响应
- `POST /v1/export`
- v1.1 流交付

### 5.2 存在隐藏

超出范围的条目必须在代理表面上隐藏。

- `GET /v1/knowledge/{id}` 对于超出范围的 id 必须返回 `404 Not Found`，而不是 `403 Forbidden`
- 过滤的条目不得对响应总数产生贡献

### 5.3 写入拒绝

如果：

- 条目的有效标签超出写入授权，或
- 条目的有效敏感性类别超过 `oamp_sensitivity_max`，或
- `source.agent_id` 与 `oamp_agent_id` 冲突

则 `POST /v1/knowledge` 必须被拒绝并返回 `403 Forbidden`。

### 5.4 导入拒绝

`POST /v1/import` 必须拒绝超过写入授权的条目，并且必须在导入响应的 `rejected` 字段中计数。

### 5.5 导出过滤

`POST /v1/export` 必须仅返回在授权下可读的条目，除非 `oamp_export_full` 存在并在直接用户身份验证下获得授权。

### 5.6 流过滤

如果后端支持 v1.1 流，则必须：

- 对于超出范围的条目省略 `knowledge_created` 和 `knowledge_updated`
- 对于代理不被允许读取的条目省略 `knowledge_deleted`

---

## 6. 能力添加

v1.3 扩展了 v1.2 治理能力块：

```json
{
  "oamp_version": "1.3.1",
  "capabilities": {
    "governance": {
      "supported": true,
      "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
      "labels_supported": true,
      "extended_provenance_supported": true,
      "withheld_stub_support": false,
      "enforcement": {
        "supported": true,
        "spec_version": "1.3.1",
        "label_hierarchy": "dotted-prefix",
        "reserved_top_level_labels": [
          "identity", "location", "health", "finance",
          "relationships", "work", "preferences",
          "creative", "beliefs", "behaviour"
        ],
        "grant_transport": ["jwt-claims", "oamp-grant-header"],
        "existence_hiding": true,
        "stream_filtering": true,
        "export_full_supported": true,
        "mediation": {
          "supported": true,
          "trusted_issuers": ["governor"]
        },
        "provenance_query": ["task_id", "context_id"]
      }
    }
  }
}
```

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `enforcement.supported` | boolean | 如果存在 `enforcement` 则必须 | 后端应用 v1.3 执行规则 |
| `enforcement.spec_version` | string | 必须 | 实现的 v1.3 规范行 |
| `enforcement.label_hierarchy` | string | 必须 | 本草案的 `dotted-prefix` |
| `enforcement.reserved_top_level_labels` | array of string | 必须 | 保留的可互操作的顶级标签 |
| `enforcement.grant_transport` | array of string | 必须 | 支持的授权传输机制 |
| `enforcement.existence_hiding` | boolean | 必须 | 是否将超出范围的 id 隐藏为 404 |
| `enforcement.stream_filtering` | boolean | 必须 | v1.1 流是否被过滤 |
| `enforcement.export_full_supported` | boolean | 必须 | 是否尊重完全导出声明 |
| `enforcement.mediation` | object | 可选 | 中介支持和受信任发行者标识符 |
| `enforcement.provenance_query` | array of string | 可选 | 支持的来源上下文过滤器（`task_id`、`context_id`） |

---

## 7. 审计日志添加

审计操作词汇增加：

- `grant_issue`
- `grant_revoke`
- `scope_denied_read`
- `scope_denied_write`

`scope_denied_read` 必须不记录受保护条目的内容，并且应避免在代理表面上记录过滤的条目 id。

---

## 8. 兼容性规则

### 8.1 v1.3 后端

- 必须继续接受 v1.0、v1.1 和 v1.2 文档
- 必须保留 v1.2 `governance` 和 `provenance`
- 必须准确宣传执行支持

### 8.2 v1.0-v1.2 客户端

- 如果不理解 `governance.enforcement` 块，则可以忽略它
- 不得仅从 `1.3.0` 版本字符串推断可移植的保留结果语义

### 8.3 没有授权的令牌

在对代理表面执行 v1.3 的后端上，未提供可用的 `oamp_read_labels` 的令牌必须被视为不读取任何内容。

部署仍然可以在可移植授权格式之外提供单独的直接用户身份验证路径。

---

## 9. 架构和 OpenAPI 工件

v1.3 草案由以下内容表示：

- `spec/v1.3/knowledge-entry.schema.json`
- `spec/v1.3/knowledge-store.schema.json`
- `spec/v1.3/openapi.yaml`

条目和存储架构在 v1.2 的基础上保持附加。v1.3 的主要新颖之处在于执行能力合同和本草案中定义的规范后端行为。