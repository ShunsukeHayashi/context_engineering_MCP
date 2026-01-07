---
description: 新しいMiyabiプロジェクト作成
---

# Miyabiプロジェクト作成

新しいMiyabiプロジェクトを作成します。GitHub連携、Agent設定、Claude Code統合を含む完全なセットアップを実行します。

## MCPツール

### `miyabi__init`
新しいMiyabiプロジェクトを作成

**パラメータ**:
- `projectName`: プロジェクト名（英数字、ハイフン、アンダースコアのみ）
- `private`: プライベートリポジトリとして作成（デフォルト: false）
- `skipInstall`: npm installをスキップ（デフォルト: false）

**使用例**:
```
パブリックプロジェクト作成:
miyabi__init({ projectName: "my-awesome-app" })

プライベートプロジェクト作成:
miyabi__init({ projectName: "my-secret-project", private: true })

npm installスキップ:
miyabi__init({ projectName: "quick-setup", skipInstall: true })
```

## 自動セットアップ内容

`miyabi__init` を実行すると、以下が自動的に実行されます:

### 1. GitHub認証
- Device Flow OAuthで安全に認証
- 必要な権限: `repo`, `workflow`, `admin:org`

### 2. GitHubリポジトリ作成
- 指定した名前でリポジトリ作成
- README.md自動生成
- .gitignore (Node.js用) 追加
- LICENSE (MIT) 追加

### 3. 組織設計原則53ラベル体系
以下のラベルカテゴリを自動作成:

| カテゴリ | ラベル数 | 例 |
|---------|---------|---|
| 🔴 緊急度 | 4 | 緊急度-高, 緊急度-中, 緊急度-低, 緊急度-即時 |
| 🔵 規模 | 4 | 規模-小, 規模-中, 規模-大, 規模-特大 |
| 🟢 種別 | 8 | type:feature, type:bug, type:refactor, type:docs |
| 🟡 状態 | 6 | status:backlog, status:in-progress, status:review |
| 🟣 責任 | 7 | owner:tech-lead, owner:po, owner:ciso |
| 🟠 エスカレーション | 5 | escalation:tech-lead, escalation:ciso |
| その他 | 19 | good first issue, help wanted, dependencies |

### 4. GitHub Actions (26ワークフロー)
以下のCI/CDワークフローを自動展開:

**基本ワークフロー**:
- `ci.yml` - CI（TypeScript, ESLint, Vitest）
- `cd.yml` - CD（Firebase自動デプロイ）
- `test.yml` - テスト実行
- `typecheck.yml` - 型チェック

**Agent自動実行**:
- `coordinator-agent.yml` - CoordinatorAgent起動
- `codegen-agent.yml` - CodeGenAgent起動
- `review-agent.yml` - ReviewAgent起動
- `pr-agent.yml` - PRAgent起動

**セキュリティ**:
- `security-scan.yml` - Dependabot, CodeQL
- `dependency-review.yml` - 依存関係レビュー

### 5. Projects V2カンバンボード
自動的に以下のカラムを持つボードを作成:

```
📋 Backlog → 🚧 In Progress → 👀 Review → ✅ Done
```

### 6. Claude Code統合
`.claude/` ディレクトリを自動生成:

```
.claude/
├── mcp.json                # MCPサーバー設定
├── commands/
│   ├── miyabi-agent.md     # /miyabi-agent
│   ├── miyabi-status.md    # /miyabi-status
│   └── miyabi-init.md      # /miyabi-init
├── hooks/
│   └── format.sh           # 自動フォーマット
└── settings.json           # Claude設定
```

### 7. ローカルクローン
作成したリポジトリをローカルに自動クローン:

```bash
git clone https://github.com/user/my-awesome-app.git
cd my-awesome-app
```

### 8. 依存関係インストール
`npm install` を自動実行（`--skip-install` を指定しない限り）

### 9. Welcome Issue作成
プロジェクト開始ガイド付きIssue #1を自動作成

## コマンドライン実行

```bash
# パブリックプロジェクト作成
npx miyabi init my-awesome-app

# プライベートプロジェクト作成
npx miyabi init my-secret-project --private

# npm installスキップ
npx miyabi init quick-setup --skip-install
```

## 実行例

```bash
$ npx miyabi init my-awesome-app

✨ Miyabi - 一つのコマンドで全てが完結

🔐 GitHub認証中...
   Device Code: XXXX-XXXX
   https://github.com/login/device でコードを入力してください

✅ GitHub認証成功

🚀 リポジトリ作成中...
   Repository: github.com/user/my-awesome-app

✅ リポジトリ作成完了

🏷️  組織設計ラベル体系セットアップ中...
   作成: 53ラベル

✅ ラベルセットアップ完了

⚙️  GitHub Actionsワークフロー展開中...
   展開: 26ワークフロー

✅ ワークフロー展開完了

📊 Projects V2ボード作成中...

✅ プロジェクトボード作成完了

📁 ローカルクローン中...
   Location: ./my-awesome-app

✅ クローン完了

📦 依存関係インストール中...

✅ インストール完了

🎉 プロジェクト作成成功！

次のステップ:
  cd my-awesome-app
  code .               # VS Code / Claude Code で開く
  npx miyabi status    # ステータス確認
  npx miyabi auto      # 全自動モード起動
```

## トラブルシューティング

### GitHub認証エラー
```bash
❌ Error: GitHub authentication failed

解決策:
1. https://github.com/login/device でコードを正しく入力
2. 必要な権限（repo, workflow）を付与
3. 認証画面が表示されない場合は、ブラウザのキャッシュをクリア
```

### リポジトリ名重複エラー
```bash
❌ Error: Repository already exists

解決策:
1. 異なるプロジェクト名を使用
2. GitHub上で既存リポジトリを削除してから再実行
```

### npm installエラー
```bash
❌ Error: npm install failed

解決策:
1. Node.js v18+ がインストールされているか確認
2. インターネット接続を確認
3. --skip-install オプションを使用して後で手動インストール
```

---

💡 **ヒント**: MCPツールを使うと、Claude Codeが対話的にパラメータを聞いて実行します。
