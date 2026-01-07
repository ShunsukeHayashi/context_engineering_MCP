---
description: Miyabi Water Spider全自動モード起動
---

# Miyabi Water Spider全自動モード

Water Spider Agent（水すまし）を起動して、GitHub Issueを自動的に検出・処理します。

## MCPツール

### `miyabi__auto`
Water Spider全自動モードを起動

**パラメータ**:
- `maxIssues`: 最大処理Issue数（デフォルト: 5）
- `interval`: ポーリング間隔（秒）（デフォルト: 60）

**使用例**:
```
全自動モード起動（デフォルト設定）:
miyabi__auto({})

最大10 Issue、30秒間隔:
miyabi__auto({ maxIssues: 10, interval: 30 })
```

## 動作フロー

```
Water Spider Agent起動
    ↓
GitHub Issueポーリング（60秒ごと）
    ↓
未処理Issueを検出
    ↓
優先順位付け（緊急度・規模・種別）
    ↓
CoordinatorAgent起動
    ↓
├─ IssueAgent（分析・Label付与）
├─ CodeGenAgent（コード生成）
├─ ReviewAgent（品質チェック）
└─ PRAgent（Draft PR作成）
    ↓
次のIssueへ（maxIssues到達まで繰り返し）
```

## 優先順位付けロジック

Water Spiderは以下の順序でIssueを処理します:

1. **緊急度が高い**: `緊急度-高`, `緊急度-即時` ラベル付き
2. **セキュリティ関連**: `security`, `vulnerability` ラベル付き
3. **ブロッカー**: `status:blocked` 以外で、依存関係が解決済み
4. **規模が小さい**: `規模-小` ラベル付き（クイックウィン）
5. **作成日時が古い**: FIFOで公平に処理

## コマンドライン実行

MCPツールの代わりにコマンドラインでも実行可能:

```bash
# デフォルト設定で起動
npx miyabi auto

# 最大Issue数と間隔を指定
npx miyabi auto --max-issues 10 --interval 30

# 1回だけ実行（ポーリングなし）
npx miyabi auto --max-issues 5 --interval 0
```

## 環境変数

`.env` ファイルに以下を設定:

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
REPOSITORY=owner/repo
DEVICE_IDENTIFIER=MacBook Pro 16-inch
```

## 停止方法

### MCPツール経由
Water Spiderはバックグラウンドで実行されないため、Claude Codeセッション終了時に自動停止します。

### CLI経由
```bash
# Ctrl+C で停止
^C
```

### プログラム的停止
```bash
# maxIssues到達で自動停止
npx miyabi auto --max-issues 3

# interval=0 で1回のみ実行
npx miyabi auto --interval 0
```

## 成功条件

Water Spiderが正常に動作するための条件:

✅ **環境**:
- `GITHUB_TOKEN` が設定済み
- `ANTHROPIC_API_KEY` が設定済み（CodeGenAgent用）
- `REPOSITORY` が正しい形式（owner/repo）

✅ **権限**:
- GitHubトークンに `repo`, `workflow` 権限
- リポジトリへの書き込み権限

✅ **Issue**:
- 未処理Issueが存在する
- Issueがブロック状態でない（`status:blocked` ラベルなし）

## 処理結果の確認

### GitHub上で確認
```bash
# 処理されたIssueを確認
gh issue list --label "status:in-progress"

# 作成されたPRを確認
gh pr list --label "automated"

# Projectsボードで進捗確認
gh project list
```

### ログで確認
```bash
# 実行ログ確認
cat .ai/logs/$(date +%Y-%m-%d).md

# 詳細レポート確認
cat .ai/parallel-reports/agents-parallel-*.json | jq
```

## エラーハンドリング

### Issue処理失敗時
Water Spiderは以下の場合にIssueをスキップして次へ進みます:

- ❌ API呼び出し失敗（3回リトライ後）
- ❌ 品質スコア不合格（<80点）
- ❌ テスト実行失敗
- ❌ エスカレーション条件に該当

失敗したIssueには自動的にコメントが追加され、適切な担当者にエスカレーションされます。

### レート制限
GitHub API レート制限に達した場合:

1. 自動的に待機（Retry-After ヘッダー参照）
2. 指数バックオフで再試行
3. 3回失敗後にエラー終了

## 使用例

### 例1: 一括処理（5件まで）

```
あなた: "全自動モードで未処理Issueを5件処理して"

Claude: [miyabi__auto({ maxIssues: 5 }) を実行]

Water Spider Agent起動
✓ Issue #123を検出
  → CoordinatorAgent起動
  → CodeGenAgent: コード生成完了
  → ReviewAgent: 品質スコア 85/100 ✅
  → PRAgent: Draft PR #124作成

✓ Issue #125を検出
  → CoordinatorAgent起動
  → ...

完了: 5件のIssueを処理しました
```

### 例2: 継続監視モード

```
あなた: "30秒ごとにIssueをチェックして、最大10件処理"

Claude: [miyabi__auto({ maxIssues: 10, interval: 30 }) を実行]

Water Spider Agent起動（継続監視モード）
[00:00] ポーリング中...
[00:30] ポーリング中... Issue #130検出 → 処理開始
[01:00] ポーリング中...
[01:30] ポーリング中... Issue #131検出 → 処理開始
...

完了: 10件のIssueを処理しました（自動停止）
```

## トラブルシューティング

### Water Spiderが起動しない
```
❌ Error: GITHUB_TOKEN is required

解決策:
1. .envファイルを確認
2. GITHUB_TOKEN=ghp_... を追加
```

### Issueが処理されない
```
⚠️  No unprocessed issues found

確認:
1. gh issue list で未処理Issueがあるか確認
2. status:blocked ラベルが付いていないか確認
3. 依存関係が解決されているか確認
```

### API制限エラー
```
❌ GitHub API rate limit exceeded

解決策:
1. レート制限リセットまで待機（通常1時間）
2. GitHub Apps トークンを使用（レート制限が緩い）
3. --interval を長くする（例: 300秒）
```

## ベストプラクティス

### 🎯 推奨設定

**通常運用**:
```bash
npx miyabi auto --max-issues 10 --interval 60
```

**夜間バッチ処理**:
```bash
npx miyabi auto --max-issues 50 --interval 0
```

**テスト・検証**:
```bash
npx miyabi auto --max-issues 1 --interval 0 --dry-run
```

### ⚠️ 注意事項

- **レート制限**: GitHub APIは1時間あたり5,000リクエスト制限があります
- **並列実行**: 複数のWater Spiderを同時実行しないでください（競合の可能性）
- **Draft PR**: 作成されるPRは全てDraftです。人間レビュー後にマージしてください

---

💡 **ヒント**: Water Spiderは「水すまし」のように、表面をさっと移動しながらタスクを次々と処理します。
