---
description: システム動作確認 - 環境・コンパイル・テストを全チェック
---

# システム動作確認

Autonomous Operationsプラットフォームの全機能を確認します。

## 確認内容

### 1. 環境設定確認

```bash
# .envファイル存在確認
ls -la .env

# 環境変数確認
cat .env | grep -v "^#" | grep -v "^$"
```

**期待結果**:
- ✅ GITHUB_TOKEN設定済み
- ✅ REPOSITORY設定済み
- ✅ DEVICE_IDENTIFIER設定済み

### 2. TypeScriptコンパイル確認

```bash
npm run typecheck
```

**期待結果**:
- ✅ エラー0件
- ✅ 全11ファイル検証完了
- ✅ Strict mode準拠

### 3. テストスイート確認

```bash
npm test -- --run
```

**期待結果**:
- ✅ 6/6 tests passing
- ✅ Duration <1秒
- ✅ CoordinatorAgent動作確認

### 4. CLI動作確認

```bash
npm run agents:parallel:exec -- --help
```

**期待結果**:
- ✅ ヘルプメッセージ表示
- ✅ 全オプション表示
- ✅ 使用例表示

## 詳細チェック

### Agent実装確認

```bash
# Agent実装ファイル確認
ls -la agents/**/*.ts

# 行数カウント
wc -l agents/**/*.ts scripts/*.ts tests/*.ts
```

**期待結果**:
- ✅ 11 TypeScriptファイル
- ✅ ~4,889行

### 依存関係確認

```bash
# node_modulesインストール確認
ls -la node_modules/ | wc -l

# パッケージ数確認
npm list --depth=0 | wc -l
```

**期待結果**:
- ✅ 258パッケージインストール済み

### GitHub Actions確認

```bash
# Workflowファイル確認
cat .github/workflows/autonomous-agent.yml | head -20

# Issue Template確認
cat .github/ISSUE_TEMPLATE/agent-task.md | head -15
```

**期待結果**:
- ✅ Workflowファイル存在
- ✅ Issue Template存在

## 統合確認

### 全チェック実行

以下のコマンドで全確認を一括実行:

```bash
echo "=== 1. 環境設定 ===" && \
ls -la .env && \
echo "=== 2. TypeScript ===" && \
npm run typecheck && \
echo "=== 3. テスト ===" && \
npm test -- --run && \
echo "=== 4. CLI ===" && \
npm run agents:parallel:exec -- --help && \
echo "=== ✅ 全確認完了 ==="
```

## チェックリスト

手動確認項目:

### 基本機能
- [ ] .envファイル設定済み
- [ ] TypeScriptコンパイル成功（0エラー）
- [ ] テストスイート合格（6/6）
- [ ] CLI正常動作

### Agent機能
- [ ] CoordinatorAgent実装済み
- [ ] CodeGenAgent実装済み
- [ ] ReviewAgent実装済み
- [ ] IssueAgent実装済み
- [ ] PRAgent実装済み
- [ ] DeploymentAgent実装済み

### インフラ
- [ ] GitHub Actions Workflow設定済み
- [ ] Issue Template作成済み
- [ ] .gitignore設定済み
- [ ] ドキュメント完備

### ドキュメント
- [ ] README.md
- [ ] DEPLOYMENT.md
- [ ] CONTRIBUTING.md
- [ ] PROJECT_SUMMARY.md
- [ ] VERIFICATION_REPORT_JP.md

## 期待される出力

### ✅ 成功例

```bash
=== 1. 環境設定 ===
-rw-r--r-- .env

=== 2. TypeScript ===
> tsc --noEmit
(エラーなし)

=== 3. テスト ===
✓ tests/coordinator.test.ts  (6 tests) 4ms
Test Files  1 passed (1)
     Tests  6 passed (6)

=== 4. CLI ===
Autonomous Operations - Parallel Executor
Usage: ...

=== ✅ 全確認完了 ===
```

### ❌ 失敗時の対処

#### TypeScriptエラー

```bash
# 依存関係再インストール
rm -rf node_modules package-lock.json
npm install
npm run typecheck
```

#### テスト失敗

```bash
# キャッシュクリア
npm test -- --clearCache
npm test -- --run
```

#### 環境変数エラー

```bash
# .env再作成
cp .env.example .env
vim .env  # API keys設定
```

## レポート出力

確認結果を `VERIFICATION_REPORT_JP.md` に記録:

```bash
echo "# 動作確認レポート" > VERIFICATION_REPORT_JP.md
echo "" >> VERIFICATION_REPORT_JP.md
echo "**日時**: $(date)" >> VERIFICATION_REPORT_JP.md
echo "" >> VERIFICATION_REPORT_JP.md
echo "## 確認結果" >> VERIFICATION_REPORT_JP.md
echo "- TypeScript: ✅" >> VERIFICATION_REPORT_JP.md
echo "- Tests: ✅" >> VERIFICATION_REPORT_JP.md
echo "- CLI: ✅" >> VERIFICATION_REPORT_JP.md
```

---

全確認項目が ✅ になれば、プロダクション準備完了です！
