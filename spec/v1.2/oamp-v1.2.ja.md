# オープンエージェントメモリプロトコル — バージョン 1.2.0

**ステータス:** 安定  
**日付:** 2026-05-09  
**著者:** ジョナサン・コンウェイ (Deep Thinking)  
**前バージョン:** なし — v1.0.0 および v1.1.0 を加算的に拡張  
**リポジトリ:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 概要

OAMP v1.2 は、v1.0.0 およびオプションの v1.1 ドラフト機能に対して **厳密に加算的** なマイナーバージョンです。以下のためのポータブルな形状を標準化します。

- `KnowledgeEntry` の管理メモリメタデータ
- `KnowledgeEntry` のより豊かなマルチソースの出所
- `GET /v1/capabilities` におけるガバナンス能力の広告
- 検索およびストリーミングサーフェス用のガバナンス対応フィルターキー

v1.2 は、保持されたまたは編集された結果文書を標準化しないことを意図しています。これらのセマンティクスは、新しいレスポンスエンベロープまたは `KnowledgeEntry` コントラクトへの破壊的変更を必要とするため、明示的に別の v2.0 設計トラックに延期されます。

この文書における「MUST」、「MUST NOT」、「REQUIRED」、「SHALL」、「SHALL NOT」、「SHOULD」、「SHOULD NOT」、「RECOMMENDED」、「MAY」、「OPTIONAL」というキーワードは、[RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) に記載されている通りに解釈されるべきです。

---

## 1. v1.0 および v1.1 との関係

v1.2 は、v1.0 のすべてのスキーマ、エンドポイント、要件、およびセマンティクスを再利用し、オプションの v1.1 能力モデルを追加し、必要なフィールドを変更することなく提供します。

新しいワイヤーレベルの追加は次のとおりです。

- OPTIONAL `governance` on `KnowledgeEntry`
- OPTIONAL `provenance` on `KnowledgeEntry`
- OPTIONAL `capabilities.governance` on `GET /v1/capabilities`
- OPTIONAL ガバナンス対応フィルターキー

文書は、v1.2 のみのフィールドを使用する場合、`oamp_version` を `"1.2.0"` に設定するべきです。v1.0 のフィールドのみを使用する文書は、最大のポータビリティのために `"1.0.0"` を使用し続けることができます。

---

## 2. スコープの分割

### 2.1 v1.2 で標準化されたもの

- ポータブルな管理メモリメタデータ
- ポータブルなより豊かな出所
- 管理メモリサポートのための能力発見
- オプションのガバナンス対応フィルタリング

### 2.2 v2.0 に明示的に延期されたもの

- 標準化された保持されたまたは編集された結果文書
- 可視エントリと保持されたスタブを含む混合結果セット
- 保持された知識のためのストリームイベントペイロード
- ポータブルな `withholding_reason` セマンティクス
- 標準化されたクロスバックエンド認可ポリシー言語

この分割は v1.2 ドラフトに対して規範的です。実装は、保持されたまたは編集されたスタブが v1.2 によって標準化されていると主張してはなりません。

---

## 3. `KnowledgeEntry` の追加

### 3.1 オプションの `governance`

`KnowledgeEntry` は、オプションの `governance` オブジェクトを取得します：

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

#### フィールド

| フィールド | タイプ | 要件 | 説明 |
|------------|--------|------|------|
| `governance` | object | MAY | 標準の管理メモリメタデータ |
| `governance.sensitivity_class` | string | MUST if `governance` present | `public`、`internal`、`confidential`、`restricted` のいずれか |
| `governance.labels` | array of string | MAY | バックエンドまたはテナント定義のガバナンスラベル |
| `governance.handling` | object | MAY | サーフェス固有のハンドリングヒント |
| `governance.handling.retrieval` | string | MAY | `governed` または `ungoverned` |
| `governance.handling.export` | string | MAY | `governed` または `ungoverned` |
| `governance.handling.stream` | string | MAY | `governed` または `ungoverned` |

`governance` オブジェクトは記述的です。ポータブルなポリシーエンジンではありません。

### 3.2 オプションの `provenance`

`KnowledgeEntry` は、既存の必須 `source` オブジェクトを保持し、オプションのより豊かな `provenance` オブジェクトを追加します：

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

#### フィールド

| フィールド | タイプ | 要件 | 説明 |
|------------|--------|------|------|
| `provenance` | object | MAY | 拡張された系譜メタデータ |
| `provenance.sources` | array | MUST if `provenance` present | 順序付きの証拠/ソースリスト |
| `provenance.sources[].session_id` | string | MUST | ソースセッション識別子 |
| `provenance.sources[].timestamp` | string | MUST | ISO 8601 取得時間 |
| `provenance.sources[].agent_id` | string | MAY | ソースエージェント識別子 |
| `provenance.sources[].turn_id` | string | MAY | ターン/メッセージローカル識別子 |
| `provenance.derived` | boolean | MAY | このエントリが複数のソースから合成されたかどうか |

既存の `source` フィールドは最小限の出所契約として残り、依然として存在する必要があります。

---

## 4. 能力の追加

v1.2 は、v1.1 の `GET /v1/capabilities` レスポンスをオプションの `capabilities.governance` オブジェクトで拡張します：

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

| フィールド | タイプ | 要件 | 説明 |
|------------|--------|------|------|
| `governance.supported` | boolean | MUST if `governance` present | バックエンドが標準化されたガバナンスフィールドを理解しているかどうか |
| `governance.sensitivity_classes` | array of string | MUST | バックエンドが受け入れるクラス |
| `governance.labels_supported` | boolean | MUST | 自由形式のラベルが保存され、保持されるかどうか |
| `governance.extended_provenance_supported` | boolean | MUST | `provenance` が保存され、保持されるかどうか |
| `governance.withheld_stub_support` | boolean | MUST | バックエンドが非標準の保持された動作を持っているかどうか |

`withheld_stub_support` は v1.2 では情報提供のみであり、ポータブルな結果形式の保証として読み取ってはなりません。

---

## 5. ガバナンス対応フィルターキー

すでにクエリフィルターやストリーミングサブスクリプションフィルターをサポートしているバックエンドは、これらのオプションのガバナンス対応キーを広告し、受け入れることができます：

| キー | タイプ | セマンティクス |
|------|--------|----------------|
| `sensitivity_class` | array of string | `governance.sensitivity_class` がセットに含まれるエントリと一致 |
| `governance_label` | array of string | リストされたガバナンスラベルのいずれかを含むエントリと一致 |

REST 検索エンドポイントでは、これらは繰り返しのクエリパラメータとして現れることがあります。ストリーミングでは、これらは `streaming.filter_keys` の広告やサブスクリプションペイロードに現れることがあります。

ガバナンスメタデータをインデックスしないバックエンドは、これらのキーを拒否または無視することがありますが、能力において正確にサポートを広告しなければなりません。

---

## 6. 互換性ルール

### 6.1 v1.2 バックエンド

- v1.0 および v1.1 文書を受け入れなければなりません。
- サポートされている場合、`governance` および `provenance` を保持しなければなりません。
- 未知のベンダー固有のメタデータ拡張を引き続き許容しなければなりません。

### 6.2 v1.0 および v1.1 クライアント

- 理解できない場合、`governance` および `provenance` を無視することができます。
- v1.2 バージョン文字列から保持されたまたは編集された結果のセマンティクスを単独で仮定してはなりません。

### 6.3 インポートとエクスポート

- 管理メモリをサポートするバックエンドは、エクスポートとインポートの間で標準化された `governance` および `provenance` を保持するべきです。
- 管理メモリをサポートしないバックエンドは、これらのフィールドが不透明に保持されるか、削除されるかを文書化するべきです。

---

## 7. スキーマと OpenAPI アーティファクト

v1.2 ドラフトは次のもので表されます：

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

これらのアーティファクトは `spec/v1/` に対して加算的であり、v1.0 の必須フィールド契約を変更しません。