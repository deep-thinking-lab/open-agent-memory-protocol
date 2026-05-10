# オープンエージェントメモリプロトコル — v1.2の管理されたメモリ

**ステータス:** 安定
**日付:** 2026-05-09
**著者:** ジョナサン・コンウェイ (Deep Thinking)
**関連実装:** `cosmictron`, `kizuna-mem`, `ultra`, `toraeru`
**依存関係:** `spec/v1/oamp-v1.md`, `spec/v1.1/oamp-v1.1.md`

---

## 1. なぜこれが存在するのか

複数のOAMPバックエンドが、第一級の管理されたメモリを必要としています：

- **kizuna-mem** は、企業グレードの感度クラス、出所を考慮したポリシー評価、および構造化された保留理由を必要としています。
- **cosmictron** は、ポリシーにスコープされたメモリとエクスポート/インポートされたガバナンスメタデータの相互運用可能な処理を必要としています。
- **ultra** は、管理されたメモリを消費および生成するため、ベンダー固有の `metadata.*` ブロブではバックエンドのポータビリティが不十分です。
- **toraeru** はOAMPと統合し、バックエンド固有のガバナンスペイロードではなく、同じポータブルメタデータ契約が必要です。

現在、OAMP v1.0/v1.1は、`metadata` 内のベンダー拡張としてのみ管理されたメモリデータを運ぶことができ、それは準拠しています。しかし：

1. ガバナンスメタデータの標準形状がありません。
2. 管理されたメモリのための標準的な能力広告がありません。
3. より豊かなマルチソースの出所のポータブル表現がありません。
4. 「保留」または「編集されたスタブ」の標準的なワイヤーレベルの概念がありません。

この提案は、最初の3つを**追加的なv1.2作業**として標準化し、4つ目は**v2.0**に明示的に延期します。なぜなら、現在のv1.xスキーマとストリーミングペイロードルールでは、破壊的変更なしにポータブルな編集されたスタブを許可しないからです。

---

## 2. 推奨事項の概要

### v1.2での標準化

- `KnowledgeEntry` にオプションの `governance` オブジェクト
- `KnowledgeEntry` にオプションの `provenance` 拡張オブジェクト
- ガバナンスサポートのための `GET /v1/capabilities` 広告
- 検索/ストリーミング用のオプションのガバナンス対応フィルタキー
- 管理されたメモリフィールドおよび往復耐性のためのコンプライアンステスト

### v2.0に延期

- 標準化された編集された/保留された結果ドキュメント
- 可視エントリと保留スタブを混在させることができる標準化されたRESTレスポンス形状
- 保留された知識のための標準化されたストリームイベントタイプ

---

## 3. なぜ保留スタブがv1.2の変更ではないのか

この提案は、意図的にv1.2で保留スタブを標準化しません。

理由：

1. v1.0では、`KnowledgeEntry.content` は必須であり、非空の文字列でなければなりません。
2. 検索/リストレスポンスは、`KnowledgeEntry` オブジェクトの配列に基づいて定義されています。
3. v1.1のストリーミングでは、`knowledge_created` と `knowledge_updated` が完全な `KnowledgeEntry` を運ぶと述べています。

つまり、ポータブルな「スタブ」は次のようになります：

```json
{
  "type": "knowledge_entry",
  "content": null,
  "withheld": true
}
```

現在のv1.xスキーマの用語では無効です。`content` をオプションまたはヌル可能にすることは、追加的な変更ではなく、破壊的なスキーマ変更になります。

したがって、正しい標準の分割は次のとおりです：

- **v1.2:** ガバナンスメタデータと発見を標準化
- **v2.0:** 保留された結果の意味を標準化

バックエンドは、v2.0の設計が確定するまで、独自の拡張でベンダー固有の保留動作を実装し続けることができます。

---

## 4. 提案されたv1.2の追加

## 4.1 `KnowledgeEntry` にオプションの `governance` フィールドを追加

新しいオプションのトップレベルフィールドを追加します：

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

### 提案されたフィールド形状

| フィールド | 型 | 要件 | 説明 |
|-------|------|-------------|-------------|
| `governance` | オブジェクト | MAY | 標準の管理されたメモリメタデータ |
| `governance.sensitivity_class` | 文字列 | `governance` が存在する場合はMUST | `public`, `internal`, `confidential`, `restricted` のいずれか |
| `governance.labels` | 文字列の配列 | MAY | バックエンドまたはテナント定義のガバナンスラベル |
| `governance.handling` | オブジェクト | MAY | サーフェス固有のガバナンスヒント |
| `governance.handling.retrieval` | 文字列 | MAY | `governed` または `ungoverned` |
| `governance.handling.export` | 文字列 | MAY | `governed` または `ungoverned` |
| `governance.handling.stream` | 文字列 | MAY | `governed` または `ungoverned` |

### 注意事項

- このフィールドは**記述的**であり、完全なポリシー言語ではありません。
- 他のバックエンドやエージェントに、知識がどのように分類されたかを伝えます。
- アクセス制御評価ルールを標準化するものではありません。
- バックエンドは、標準の `governance` フィールドに加えて、より豊かなローカルポリシー構造を `metadata` にマッピングすることができます。

## 4.2 `KnowledgeEntry` にオプションの拡張 `provenance` フィールドを追加

`source` はそのままにして、オプションのより豊かな出所構造を追加します：

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

### 提案されたフィールド形状

| フィールド | 型 | 要件 | 説明 |
|-------|------|-------------|-------------|
| `provenance` | オブジェクト | MAY | 拡張された系譜メタデータ |
| `provenance.sources` | 配列 | `provenance` が存在する場合はMUST | 順序付けられた証拠/ソースリスト |
| `provenance.sources[].session_id` | 文字列 | MUST | ソースセッション識別子 |
| `provenance.sources[].timestamp` | 文字列 | MUST | ISO 8601取得時間 |
| `provenance.sources[].agent_id` | 文字列 | MAY | ソースエージェント識別子 |
| `provenance.sources[].turn_id` | 文字列 | MAY | ターン/メッセージローカル識別子 |
| `provenance.derived` | ブール値 | MAY | このエントリが複数のソースから合成されたかどうか |

### 注意事項

- `source` は必須であり、最小限の出所契約として残ります。
- `provenance` は、マージ、合成、または証拠チェーンをサポートするバックエンドのためのより豊かな相互運用可能な系譜拡張です。

## 4.3 ガバナンス能力の広告

`/v1/capabilities.capabilities` の下にオプションの `governance` オブジェクトを追加します：

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

### 提案されたフィールド

| フィールド | 型 | 要件 | 説明 |
|-------|------|-------------|-------------|
| `governance.supported` | ブール値 | `governance` が存在する場合はMUST | バックエンドが標準化されたガバナンスフィールドを理解しているかどうか |
| `governance.sensitivity_classes` | 文字列の配列 | MUST | バックエンドが受け入れるクラス |
| `governance.labels_supported` | ブール値 | MUST | 自由形式のガバナンスラベルが保存/保持されるかどうか |
| `governance.extended_provenance_supported` | ブール値 | MUST | `provenance` が保存/保持されるかどうか |
| `governance.withheld_stub_support` | ブール値 | MUST | バックエンドに非標準の保留スタブ動作があるかどうか |

`withheld_stub_support` はv1.2では情報提供のみです。標準化されたワイヤフォーマットを意味するものではありません。

## 4.4 オプションのガバナンス対応フィルタ

バックエンドがフィルタ広告をサポートする場合、これらのオプションのキーを標準化します：

| キー | 型 | セマンティクス |
|-----|------|-----------|
| `sensitivity_class` | 文字列の配列 | `governance.sensitivity_class` がセットに含まれるエントリと一致 |
| `governance_label` | 文字列の配列 | リストされたガバナンスラベルのいずれかを含むエントリと一致 |

これは次のことに適用されます：

- バックエンド固有のクエリモデルによってサポートされるREST検索
- ストリーミングがサポートされている場合の `streaming.filter_keys`

これらのキーはオプションです。すべてのバックエンドがガバナンスメタデータをインデックスするわけではありません。

---

## 5. スキーマとOpenAPIへの影響

この提案は、新しいマイナーバージョンスキーマを必要とします。なぜなら、現在のv1.0 JSONスキーマは `KnowledgeEntry` と `KnowledgeStore` エントリアイテムに `additionalProperties: false` を設定しているからです。

したがって、v1.2の作業には次が含まれなければなりません：

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

追加的なオプションフィールド：

- `governance`
- `provenance`

v1.2では必須フィールドの変更はありません。

---

## 6. 互換性ルール

### v1.2バックエンドの動作

- v1.0およびv1.1のドキュメントを受け入れなければなりません。
- 提供された場合、`governance` と `provenance` を保持しなければなりません。ただし、文書化されたポリシーまたはストレージ制約が明示的にそれらを拒否する場合を除きます。
- 不明な追加のベンダーメタデータは以前のように無視しなければなりません。

### v1.0 / v1.1クライアントの動作

- v1.0またはv1.1のクライアントは、理解できない場合、`governance` と `provenance` を無視することができます。
- これは安全です。なぜなら、両方ともオプションの追加フィールドだからです。

### インポート/エクスポートの期待

- ガバナンスをサポートするバックエンドは、エクスポート/インポートの間に標準化されたガバナンスフィールドを保持するべきです。
- ガバナンスをサポートしないバックエンドは、ドキュメントを受け入れ、フィールドを不透明なデータとして保持するか、ドロップされることを文書化するべきです。

---

## 7. v1.2の非目標

以下は、この提案の範囲外であることが明示されています：

- 標準化された許可/拒否ポリシー言語
- クロスバックエンドの認可セマンティクス
- 標準化された `withholding_reason`
- 標準化された編集された `KnowledgeEntry` スタブ形状
- マルチユーザーサブスクリプションセマンティクス

それらは次のいずれかを必要とします：

- 別のv2.0設計、または
- 現在のv1.xの期待に合わない新しい非 `KnowledgeEntry` レスポンス/イベントエンベロープ。

---

## 8. コンプライアンスの追加

v1.2が実現した場合、次のコンプライアンスケースを追加します：

- `POST /v1/knowledge` が `governance` を受け入れる
- `POST /v1/knowledge` が `provenance` を受け入れる
- `GET /v1/knowledge/:id` が標準化されたガバナンスフィールドを往復する
- `POST /v1/import` がサポートされている場合、ガバナンス/出所を保持する
- `/v1/capabilities` がガバナンスサポートを正確に広告する

v1.2で保留スタブのコンプライアンステストを追加してはいけません。

---

## 9. 提案されたアップストリームの問題分解

### 問題 1: 管理されたメモリのスコープ分割を承認

決定し、文書化します：

- v1.2はガバナンスメタデータ + 発見を標準化する
- v2.0は保留/編集された結果の意味を扱う

### 問題 2: v1.2スキーマに `governance` と `provenance` を追加

ファイル：

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`
- 参照型ライブラリ

### 問題 3: 能力広告とフィルタキー

ファイル：

- `spec/v1.2/oamp-v1.2.md`
- `spec/v1.2/openapi.yaml`
- v1.1の能力テキストが再利用または上書きされる場合

### 問題 4: コンプライアンススイートのカバレッジ

ファイル：

- `reference/compliance/README.md`
- `reference/compliance/src/oamp_compliance/tests/`

### 問題 5: 参照バックエンドのサポート

ファイル：

- `reference/server/`
- 言語参照型

### 問題 6: 保留結果のためのv2.0 RFC

次のための別の設計トラックを開きます：

- 破壊的でないエンベロープオプションとメジャーバージョンスキーマの変更
- ポリシーによる保留のためのRESTセマンティクス
- 保留された更新のためのストリームセマンティクス
- `withholding_reason` のポータビリティ

---

## 10. 推奨事項

この提案を作業方向として採用します：

1. v1.2で管理されたメモリメタデータを標準化する、
2. v1.2でより豊かな出所を標準化する、
3. 保留/編集の意味をv1.2から除外する、
4. ポータブルな保留結果のための別のv2.0 RFCを開く。

これにより、`cosmictron`、`kizuna-mem`、`ultra`、および `toraeru` に共通の相互運用可能なターゲットが与えられ、現在のv1.xの `KnowledgeEntry` 形状が我々が望むすべての管理されたメモリの動作をすでに表現できると偽ることはありません。