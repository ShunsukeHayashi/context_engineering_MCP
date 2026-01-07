# YAML Context Engineering Agent - 使用例

## 概要
このテンプレートは、YAML形式でコンテキスト情報を構造化抽出する自律エージェントを設計するためのものです。

## 基本的な使用方法

### 1. テンプレート変数の設定

```json
{
  "agent_name": "DocumentAnalysisAgent",
  "agent_description": "技術文書からYAML形式でコンテキスト情報を抽出し、構造化する専門エージェント",
  "user_input": "新しいAPI設計ドキュメントを分析して、エンドポイント情報をYAML形式で抽出してください",
  "context_requirement": "RESTful API仕様書から各エンドポイントの詳細情報を抽出し、標準化されたYAML構造で出力する必要があります",
  "content_guidelines": "- 明確な階層構造を持つYAML形式で出力\n- エンドポイントごとに必要な情報を網羅\n- コメント付きで理解しやすくする"
}
```

### 2. 実行結果例

#### 入力ドキュメント
```
POST /api/users
Creates a new user account
Parameters: name (string), email (string), password (string)
Response: User object with ID

GET /api/users/{id}
Retrieves user information
Parameters: id (integer)
Response: User object
```

#### エージェントによる出力
```yaml
api_specification:
  name: "User Management API"
  version: "1.0.0"
  base_url: "/api"
  
  endpoints:
    - endpoint: "/users"
      method: "POST"
      description: "Creates a new user account"
      parameters:
        - name: "name"
          type: "string"
          required: true
          description: "User's full name"
        - name: "email"
          type: "string"
          required: true
          description: "User's email address"
        - name: "password"
          type: "string"
          required: true
          description: "User's password"
      responses:
        - status_code: 201
          description: "User created successfully"
          schema: "User"
          
    - endpoint: "/users/{id}"
      method: "GET"
      description: "Retrieves user information"
      parameters:
        - name: "id"
          type: "integer"
          required: true
          location: "path"
          description: "Unique user identifier"
      responses:
        - status_code: 200
          description: "User information retrieved"
          schema: "User"
        - status_code: 404
          description: "User not found"

  schemas:
    User:
      type: "object"
      properties:
        id:
          type: "integer"
          description: "Unique identifier"
        name:
          type: "string"
          description: "User's full name"
        email:
          type: "string"
          description: "User's email address"
        created_at:
          type: "string"
          format: "datetime"
          description: "Account creation timestamp"
```

## 高度な使用例

### セキュリティ分析用設定

```json
{
  "agent_name": "SecurityAnalysisAgent",
  "agent_description": "セキュリティドキュメントから脅威情報をYAML形式で抽出する専門エージェント",
  "user_input": "ペネトレーションテスト報告書から発見された脆弱性を分析し、YAML形式で構造化してください",
  "context_requirement": "各脆弱性について、CVSS スコア、影響範囲、対策方法を含む包括的な情報を抽出する",
  "content_guidelines": "- CVSSスコアによる重要度分類\n- 対策の優先順位付け\n- 技術的詳細の構造化"
}
```

### ビジネス分析用設定

```json
{
  "agent_name": "BusinessAnalysisAgent",
  "agent_description": "企業レポートから業績指標をYAML形式で抽出する専門エージェント",
  "user_input": "四半期業績報告書から売上、利益、成長率などの指標を抽出してください",
  "context_requirement": "財務数値、前年同期比、予算対実績比較などの情報を含む包括的な分析",
  "content_guidelines": "- 時系列データの構造化\n- 比較分析のための標準化\n- トレンド分析用メタデータ"
}
```

## 応用パターン

### 1. マルチドキュメント分析
複数のドキュメントを一度に処理し、統合されたYAML出力を生成

### 2. インクリメンタル更新
既存のYAML構造に新しい情報を段階的に追加

### 3. バリデーション機能
生成されたYAMLの品質チェックと改善提案

### 4. カスタムスキーマ
特定の業界や用途に特化したYAML構造の定義

## ベストプラクティス

1. **明確な指示**: agent_descriptionで具体的な役割を定義
2. **文脈の提供**: context_requirementで必要な背景情報を明示
3. **品質基準**: content_guidelinesで出力品質の要件を設定
4. **反復改善**: 出力結果を基にテンプレート変数を調整

## トラブルシューティング

### よくある問題と解決策

**問題**: YAML構造が一貫しない
**解決策**: content_guidelinesでより詳細な構造定義を提供

**問題**: 重要な情報が欠落する
**解決策**: context_requirementで必須項目を明確に指定

**問題**: 出力が冗長すぎる
**解決策**: user_inputで具体的な抽出範囲を限定

## 関連テンプレート

- **AI Multi-Agent Workflow**: 複数エージェントでの協調処理
- **Command Stack**: 段階的な処理フローの実行
- **Code Review**: 技術文書の品質チェック