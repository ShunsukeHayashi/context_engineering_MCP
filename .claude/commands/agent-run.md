---
description: Autonomous Agent実行 - Issue自動処理パイプライン
---

# Autonomous Agent実行

GitHub IssueをAutonomous Agentシステムで自動処理します。

## 実行フロー

```
Issue作成/検出
    ↓
CoordinatorAgent（タスク分解・DAG構築）
    ↓ 並行実行
├─ IssueAgent（Issue分析・Label付与）
├─ CodeGenAgent（コード生成）
├─ ReviewAgent（品質チェック≥80点）
└─ PRAgent（PR作成）
    ↓
Draft PR作成
    ↓
人間レビュー待ち
```

## コマンド

### 単一Issue処理

```bash
npm run agents:parallel:exec -- --issue 123
```

### 複数Issue並行処理

```bash
npm run agents:parallel:exec -- --issues 123,124,125 --concurrency 3
```

### Dry run（確認のみ、変更なし）

```bash
npm run agents:parallel:exec -- --issue 123 --dry-run
```

### ヘルプ表示

```bash
npm run agents:parallel:exec -- --help
```

## オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--issue <number>` | 単一Issue番号 | - |
| `--issues <n1,n2,...>` | 複数Issue番号（カンマ区切り） | - |
| `--concurrency <number>` | 並行実行数 | 2 |
| `--dry-run` | 実行のみ（変更なし） | false |
| `--log-level <level>` | ログレベル | info |

## 環境変数

必須環境変数（`.env`ファイル）:

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
REPOSITORY=owner/repo
DEVICE_IDENTIFIER=MacBook Pro 16-inch
```

## 成功条件

✅ **必須**:
- Issue分析完了
- コード生成成功
- 品質スコア ≥80点
- Draft PR作成

✅ **品質**:
- TypeScriptエラー 0件
- ESLintエラー 0件
- セキュリティスキャン合格
- テストカバレッジ ≥80%

## エスカレーション

以下の場合、自動エスカレーション:

| 条件 | エスカレーション先 | 重要度 |
|------|------------------|--------|
| アーキテクチャ問題 | TechLead | Sev.2-High |
| セキュリティ脆弱性 | CISO | Sev.1-Critical |
| ビジネス優先度 | PO | Sev.3-Medium |
| 循環依存検出 | TechLead | Sev.2-High |

## 実行例

### 例1: 単一Issue処理

```bash
$ npm run agents:parallel:exec -- --issue 270

🤖 Autonomous Operations - Parallel Executor

✅ Configuration loaded
   Device: MacBook Pro 16-inch
   Repository: ShunsukeHayashi/Autonomous-Operations
   Concurrency: 2

✅ Fetched Issue #270: Add user authentication

================================================================================
🚀 Executing Issue #270: Add user authentication
================================================================================

[CoordinatorAgent] 🔍 Decomposing Issue #270
[CoordinatorAgent]    Found 4 tasks
[CoordinatorAgent] 🔗 Building task dependency graph (DAG)
[CoordinatorAgent]    Graph: 4 nodes, 0 edges, 1 levels
[CoordinatorAgent] ✅ No circular dependencies found

[CodeGenAgent] 🧠 Generating code with Claude AI
[CodeGenAgent]    Generated 3 files

[ReviewAgent] 📊 Calculating quality score
[ReviewAgent]    Score: 85/100 ✅

[PRAgent] 🚀 Creating Pull Request
[PRAgent] ✅ PR created: #271

✅ Issue #270 completed successfully
   Duration: 45,234ms
```

### 例2: Dry run

```bash
$ npm run agents:parallel:exec -- --issue 270 --dry-run

🤖 Autonomous Operations - Parallel Executor
   Dry Run: Yes (no changes will be made)

[実行のみ、ファイル書き込みなし]
```

## トラブルシューティング

### API Key エラー

```bash
❌ Error: ANTHROPIC_API_KEY is required for CodeGenAgent

解決策:
1. .envファイルを確認
2. ANTHROPIC_API_KEY=sk-ant-... を追加
```

### GitHub API エラー

```bash
❌ Failed to fetch issue #270: Not Found

解決策:
1. Issue番号が正しいか確認
2. GITHUB_TOKEN権限を確認（repo, workflow）
3. REPOSITORYが正しいか確認
```

### 品質スコア不合格

```bash
❌ Quality score: 75/100 (Failed)

エスカレーション:
→ TechLeadにエスカレーションされました
→ Issue #270にコメントが追加されます
```

## ログ確認

```bash
# 実行ログ
cat .ai/logs/$(date +%Y-%m-%d).md

# 実行レポート
cat .ai/parallel-reports/agents-parallel-*.json | jq
```

## GitHub Actions連携

GitHub Actionsから自動実行される場合:

```yaml
- name: Execute CoordinatorAgent
  run: |
    npm run agents:parallel:exec -- \
      --issue ${{ needs.check-trigger.outputs.issue_number }} \
      --concurrency 3 \
      --log-level info
```

---

実行後、Draft PRが作成されるので、人間がレビューして承認してください。
