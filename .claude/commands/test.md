---
description: プロジェクト全体のテストを実行
---

# テスト実行

プロジェクト全体のTypeScriptコンパイルとテストスイートを実行します。

## 実行内容

1. **TypeScript型チェック**
   ```bash
   npm run typecheck
   ```
   - Strict mode有効
   - 全11ファイル検証
   - エラー0件が目標

2. **Vitestテストスイート**
   ```bash
   npm test
   ```
   - CoordinatorAgentテスト
   - DAG構築テスト
   - 循環依存検出テスト

## 期待される結果

✅ **TypeScript**: エラー0件
✅ **Tests**: 6/6 passing
✅ **Duration**: <1秒

## テスト対象

- `tests/coordinator.test.ts`
  - Task decomposition
  - DAG construction
  - Circular dependency detection
  - Agent assignment
  - Execution plan

## カバレッジ確認

```bash
npm run test:coverage
```

## 失敗時の対処

### TypeScriptエラー
```bash
# エラー詳細確認
npm run typecheck

# 型定義確認
cat agents/types/index.ts
```

### テスト失敗
```bash
# 詳細モードで実行
npm test -- --reporter=verbose

# 特定のテストのみ
npm test -- tests/coordinator.test.ts
```

## CI/CD統合

GitHub Actionsで自動実行されます：

```yaml
- name: Run TypeScript compilation check
  run: npm run typecheck

- name: Run tests
  run: npm test
```

---

実行完了後、全テストが合格していることを確認してください。
