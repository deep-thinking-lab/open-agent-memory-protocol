# オープンエージェントメモリプロトコル — バージョン 1.3.0 (ドラフト)

**ステータス:** ドラフト (提案されたマイナーバージョン)  
**日付:** 2026-05-07  
**著者:** ジョナサン・コンウェイ (Deep Thinking)  
**前バージョン:** なし — v1.0.0、v1.1.0、および v1.2.0 を加算的に拡張  
**リポジトリ:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 概要

OAMP v1.3 は v1.0.0 とオプションの v1.1 および v1.2 ドラフト機能に対して **厳密に加算的** なマイナーバージョンです。これは、v1.2 で記述的に導入された管理メモリの **強制** レイヤーを標準化します。

v1.2 では以下が標準化されました：

- `governance.sensitivity_class`
- `governance.labels`
- `governance.handling`
- より豊かな `provenance`
- ガバナンス機能の発見

v1.3 は、同じユーザーの複数のエージェントが同じバックエンドにアクセスする際に、バックエンドがこれらのフィールドで何を行うべきかを定義します。以下が標準化されます：

- ポータブルエージェントグラントクレーム
- 階層的ラベルマッチング規約
- 読み取り、書き込み、インポート、エクスポート、およびストリームフィルタリングルール
- エージェント表面での存在隠蔽
- プロヴェナンスへのエージェントアイデンティティバインディング
- 監査ログの追加
- 強制サポートのための機能広告

v1.3 は **省略ベース** のままです。ポータブルな保留または編集された結果文書は **標準化されません**。その作業は別の v2.0 トラックに先送りされます。

この文書における「MUST」、「MUST NOT」、「REQUIRED」、「SHALL」、「SHALL NOT」、「SHOULD」、「SHOULD NOT」、「RECOMMENDED」、「MAY」、「OPTIONAL」というキーワードは、[RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) に記載されている通りに解釈されるべきです。

---

## 1. 以前のバージョンとの関係

v1.3 は、すべての v1.0 スキーマ、エンドポイント、要件、および意味論ルール、さらにオプションの v1.1 機能モデルと加算的な v1.2 管理メモリメタデータモデルを再利用します。

v1.3 における唯一の新しいワイヤーレベルの追加は以下です：

- OPTIONAL `capabilities.governance.enforcement` on `GET /v1/capabilities`
- JWT クレームまたは `OAMP-Grant` 用のポータブルエージェントグラントクレーム形式
- 既存の v1.2 `governance` フィールドを消費する規範的なバックエンド動作

v1.3 は **新しい `KnowledgeEntry` フィールド** および **新しい `KnowledgeStore` フィールド** を導入しません。

v1.0-v1.2 エントリ/ストアフィールドのみを使用する文書は、`"1.2.0"` を `oamp_version` として使用し続けることができます。v1.3 ドラフトラインを広告したい文書およびレスポンスは、`"1.3.0"` を使用することができます。

---

## 2. スコープの分割

### 2.1 v1.3 で標準化されたもの

- ポータブルなエージェントごとのグラントクレーム
- 階層的なガバナンスラベル強制の意味論
- v1.2 ガバナンスハンドリングヒントの運用的意味
- 読み取りフィルタリング
- 書き込み拒否
- インポート拒否の会計
- エクスポートフィルタリングおよび `oamp_export_full`
- v1.1 表面でのストリームフィルタリング
- エージェント表面での存在隠蔽
- `oamp_agent_id` へのプロヴェナンスバインディング
- ガバナンス強制機能の広告
- グラントおよびスコープイベントの監査アクション名

### 2.2 明示的に v2.0 に先送りされたもの

- 標準化された保留または編集された結果文書
- 可視エントリと保留スタブを含む混合結果セット
- ポータブルな `withholding_reason` 意味論
- 保留された知識を明示的に表すストリームペイロード
- ポータブルなクロスバックエンド認可ポリシー言語

実装は、v1.3 が保留または編集されたスタブ文書を標準化していると主張してはなりません。

---

## 3. v1.2 ガバナンスメタデータの運用再利用

v1.3 は **新しいエントリレベルのガバナンスフィールド** を追加しません。代わりに、v1.2 フィールドを運用可能にします。

### 3.1 `governance.sensitivity_class`

v1.2 の列挙型は次のように順序付けられています：

`public < internal < confidential < restricted`

エージェントグラントは `oamp_sensitivity_max` を持ちます。実効的な `sensitivity_class` がグラントの上限を超えるエントリはフィルタリングまたは拒否されます。

`governance` が存在しない場合、実効クラスは強制目的のために `internal` です。

### 3.2 `governance.labels`

v1.3 は強制に使用される階層的ラベル規約を導入します。

- ラベルは、`^[a-z][a-z0-9]*(\\.[a-z][a-z0-9_]*)*$` に一致するドット付きの小文字 ASCII パスであるべきです
- 階層的プレフィックスマッチングが適用されます
- `health` のグラントは `health.condition` および `health.condition.diagnosis` に一致します

ベンダー間の相互運用性のための予約されたトップレベルラベル：

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

ベンダー固有の拡張は `x.<vendor>.<...>` の下に存在するべきです。

階層的規約に一致しないラベルは、依然として有効な記述的 v1.2 ラベルですが、v1.3 を強制するバックエンドはそれらを不透明な正確なマッチ値として扱うべきです。

`governance.labels` が存在しないか空である場合、実効ラベルセットは強制目的のために `["behaviour"]` です。

### 3.3 `governance.handling`

v1.2 の `handling` ヒントは v1.3 で負荷を支えるものになります：

- `retrieval: "governed"` は読み取りパスがグラントフィルタリングを適用することを意味します
- `retrieval: "ungoverned"` はエントリを読み取りパスフィルタリングから免除します
- `export: "governed"` はエクスポートパスがグラントフィルタリングを適用することを意味します
- `export: "ungoverned"` はエントリをエクスポートパスフィルタリングから免除します
- `stream: "governed"` は v1.1 ストリーミングパスがグラントフィルタリングを適用することを意味します
- `stream: "ungoverned"` はエントリをストリームフィルタリングから免除します
- `mediation: "required"` はエントリへのアクセスに信頼できる仲介発行者からの有効なグラントが必要であることを意味します
- `mediation: "optional"` は仲介制約が表現されていないことを意味します

`governance` が存在し、ハンドリング値が省略されている場合、その表面に対する実効デフォルトは `governed` です。

`mediation` が省略されている場合、実効デフォルトは `optional` です。

---

## 4. エージェントグラントクレーム

### 4.1 JWT クレームの形状

ベアラ認証が JWT を使用する場合、トークンは以下の追加クレームを持ちます：

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

| クレーム | 要件 | 説明 |
|----------|------|------|
| `oamp_agent_id` | MUST | 呼び出しエージェントの安定した識別子 |
| `oamp_grant_id` | MUST | グラントインスタンスの安定した識別子 |
| `oamp_read_labels` | MUST | エージェントが読み取ることができるラベル |
| `oamp_write_labels` | MUST | エージェントが書き込むことができるラベル |
| `oamp_sensitivity_max` | MUST | 読み取り/書き込み可能な最高の感度クラス |
| `oamp_export_full` | MAY | フルのフィルタリングされていないエクスポートが許可されているかどうか |
| `iss` | 必要な仲介リソースの場合は MUST; それ以外は MAY | グラントを発行した権限の安定した識別子 |
| `oamp_mediation_required` | MAY | このグラントが仲介フローを意図していることを示します |
| `oamp_task_id` | MAY | エージェントが実行するために提供された作業単位の識別子 |
| `oamp_context_id` | MAY | タスクの上位にある不透明なグルーピング識別子 |

空の `oamp_read_labels` は読み取りなしを意味します。

### 4.2 `OAMP-Grant` ヘッダー

JWT ベアラトークンを使用しないデプロイメントでは、同じクレームオブジェクトを `OAMP-Grant` ヘッダーで伝達することができます。ヘッダー値はクレームオブジェクトに対するコンパクトな JWS でなければなりません。

### 4.3 プロヴェナンスバインディング

v1.3 グラントの下で書き込みが行われるとき、バックエンドは以下を検証しなければなりません：

- `entry.source.agent_id == oamp_agent_id`、`source.agent_id` が存在する場合

`provenance.sources[*].agent_id` を持つエントリについて、バックエンドは呼び出しグラントまたはローカルトラストモデルに対して各リストされた `agent_id` を検証するべきです。

v1.3.1 グラントの下で `oamp_task_id` または `oamp_context_id` を持つ書き込みが行われるとき、バックエンドはそれらの値を `provenance.sources[*].task_id` および `provenance.sources[*].context_id` にスタンプするべきです。これらのフィールドは記述的な帰属のみであり、アクセスを拡大してはなりません。

---

## 5. バックエンド強制ルール

`governance.enforcement.supported: true` を広告するバックエンドは、これらのルールを適用しなければなりません。

### 5.1 読み取りフィルタリング

エントリは、管理された読み取りを通過するのは次の条件を満たす場合のみです：

1. 実効的な取得ハンドリングが免除されておらず、かつ
2. いずれかの実効エントリラベルがいくつかの付与された読み取りラベルによって一致し、かつ
3. 実効的な感度クラスが `oamp_sensitivity_max` 以下である

失敗したエントリは以下に表示されてはなりません：

- `GET /v1/knowledge/{id}`
- `GET /v1/knowledge`
- 検索レスポンス
- `POST /v1/export`
- v1.1 ストリーム配信

### 5.2 存在隠蔽

範囲外のエントリはエージェント表面で隠されなければなりません。

- 範囲外の ID に対して `GET /v1/knowledge/{id}` は `404 Not Found` を返さなければならず、`403 Forbidden` ではありません
- フィルタリングされたエントリはレスポンスタイトルに寄与してはなりません

### 5.3 書き込み拒否

`POST /v1/knowledge` は次の条件で `403 Forbidden` で拒否されなければなりません：

- エントリの実効ラベルが書き込みグラントの範囲外である場合、または
- エントリの実効感度クラスが `oamp_sensitivity_max` を超える場合、または
- `source.agent_id` が `oamp_agent_id` と矛盾する場合

### 5.4 インポート拒否

`POST /v1/import` は書き込みグラントを超えるエントリを拒否し、それらをインポートレスポンスの `rejected` フィールドにカウントしなければなりません。

### 5.5 エクスポートフィルタリング

`POST /v1/export` は、グラントの下で読み取れるエントリのみを返さなければなりません。ただし、`oamp_export_full` が存在し、直接ユーザー認証の下で許可されている場合は除きます。

### 5.6 ストリームフィルタリング

バックエンドが v1.1 ストリーミングをサポートしている場合、次のことを行わなければなりません：

- 範囲外のエントリに対して `knowledge_created` および `knowledge_updated` を省略する
- エージェントが読み取ることを許可されていないエントリに対して `knowledge_deleted` を省略する

---

## 6. 機能の追加

v1.3 は v1.2 ガバナンス機能ブロックを拡張します：

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

| フィールド | 型 | 要件 | 説明 |
|------------|----|------|------|
| `enforcement.supported` | boolean | `enforcement` が存在する場合は MUST | バックエンドが v1.3 強制ルールを適用する |
| `enforcement.spec_version` | string | MUST | 実装された v1.3 スペックライン |
| `enforcement.label_hierarchy` | string | MUST | このドラフトのための `dotted-prefix` |
| `enforcement.reserved_top_level_labels` | array of string | MUST | 予約された相互運用可能なトップレベルラベル |
| `enforcement.grant_transport` | array of string | MUST | サポートされているグラント輸送メカニズム |
| `enforcement.existence_hiding` | boolean | MUST | 範囲外の ID が 404 として隠されるかどうか |
| `enforcement.stream_filtering` | boolean | MUST | v1.1 ストリームがフィルタリングされるかどうか |
| `enforcement.export_full_supported` | boolean | MUST | フルエクスポートクレームが尊重されるかどうか |
| `enforcement.mediation` | object | MAY | 仲介サポートと信頼できる発行者識別子 |
| `enforcement.provenance_query` | array of string | MAY | サポートされているプロヴェナンスコンテキストフィルター (`task_id`, `context_id`) |

---

## 7. 監査ログの追加

監査アクション語彙が次のように増えます：

- `grant_issue`
- `grant_revoke`
- `scope_denied_read`
- `scope_denied_write`

`scope_denied_read` は保護されたエントリの内容をログに記録してはならず、エージェント表面でフィルタリングされたエントリ ID のログ記録を避けるべきです。

---

## 8. 互換性ルール

### 8.1 v1.3 バックエンド

- v1.0、v1.1、および v1.2 文書を引き続き受け入れなければなりません
- v1.2 `governance` および `provenance` を保持しなければなりません
- 強制サポートを正確に広告しなければなりません

### 8.2 v1.0-v1.2 クライアント

- 理解できない場合は `governance.enforcement` ブロックを無視することができます
- `1.3.0` バージョン文字列だけからポータブルな保留結果の意味を推測してはなりません

### 8.3 グラントのないトークン

エージェント表面に対して v1.3 を強制するバックエンドでは、使用可能な `oamp_read_labels` を提示しないトークンは読み取りなしとして扱われなければなりません。

デプロイメントは、ポータブルグラント形式の外で別の直接ユーザー認証パスを提供することができます。

---

## 9. スキーマおよび OpenAPI アーティファクト

v1.3 ドラフトは次のもので表されます：

- `spec/v1.3/knowledge-entry.schema.json`
- `spec/v1.3/knowledge-store.schema.json`
- `spec/v1.3/openapi.yaml`

エントリおよびストアスキーマは v1.2 に対して加算的なままです。v1.3 の主な新規性は、強制機能契約とこのドラフトで定義された規範的なバックエンド動作です。