---
description: Firebase/Cloud デプロイ実行
---

# Deploy Command

DeploymentAgentを使用してアプリケーションをデプロイします。

## 使用方法

```bash
/deploy [environment]
```

## パラメータ

- `environment` (オプション): デプロイ環境
  - `staging` (デフォルト): ステージング環境
  - `production`: プロダクション環境

## 実行内容

### 1. Pre-Deployment Checks

```bash
# TypeScriptコンパイル確認
npm run typecheck

# テスト実行
npm test -- --run

# ビルド実行
npm run build
```

### 2. Firebase Deploy

```bash
# Staging
firebase deploy --only hosting:staging

# Production (確認プロンプト付き)
firebase deploy --only hosting:production
```

### 3. Health Check

デプロイ後、ヘルスチェックURLに自動アクセスして動作確認:

```bash
curl -f https://your-app.web.app/health
```

### 4. Rollback (失敗時)

ヘルスチェックが失敗した場合、自動的に前のバージョンにロールバック:

```bash
firebase hosting:rollback
```

## デプロイフロー

```mermaid
graph TD
    A[/deploy実行] --> B[Pre-deployment Checks]
    B --> C{テスト合格?}
    C -->|No| D[エラー: デプロイ中止]
    C -->|Yes| E[ビルド実行]
    E --> F[Firebase Deploy]
    F --> G[Health Check]
    G --> H{正常?}
    H -->|No| I[自動Rollback]
    H -->|Yes| J[デプロイ完了]
    I --> K[Tech Leadにエスカレーション]
```

## 必要な環境変数

```bash
# .env
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_TOKEN=your-firebase-token  # CI/CD用
```

## Firebase Tokenの取得方法

```bash
# ローカル開発
firebase login

# CI/CD用トークン
firebase login:ci
# 表示されたトークンを FIREBASE_TOKEN に設定
```

## GitHub Secretsの設定

GitHub Actions経由でデプロイする場合:

1. Repository Settings → Secrets and variables → Actions
2. 以下のSecretsを追加:
   - `FIREBASE_TOKEN`: Firebase CI token
   - `ANTHROPIC_API_KEY`: Claude API key (既存)

## デプロイ設定

### firebase.json

```json
{
  "hosting": [
    {
      "target": "staging",
      "public": "dist",
      "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
      "rewrites": [
        {
          "source": "**",
          "destination": "/index.html"
        }
      ]
    },
    {
      "target": "production",
      "public": "dist",
      "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
      "rewrites": [
        {
          "source": "**",
          "destination": "/index.html"
        }
      ]
    }
  ]
}
```

### .firebaserc

```json
{
  "projects": {
    "default": "your-firebase-project-id"
  },
  "targets": {
    "your-firebase-project-id": {
      "hosting": {
        "staging": ["your-app-staging"],
        "production": ["your-app-production"]
      }
    }
  }
}
```

## Production デプロイの確認プロンプト

Productionへのデプロイ時は、必ず確認プロンプトが表示されます:

```
⚠️  Production Deploy Warning

環境: production
バージョン: v1.2.3
影響: 本番環境のすべてのユーザー

続行しますか? (yes/no):
```

`yes` と入力した場合のみデプロイが実行されます。

## エラーハンドリング

### デプロイ失敗時

```
❌ Deployment Failed

原因: Health check failed (HTTP 500)
アクション: 自動Rollback実行中...

✅ Rollback完了
前バージョン (v1.2.2) に復旧しました

🔺 Escalation: Tech Leadに通知済み
Slackチャンネル: #incidents
```

### Rollback失敗時

```
❌ Rollback Failed

原因: Previous version not found
アクション: 手動対応が必要

🚨 Escalation: CTO/CISO に通知
Severity: Sev.1-Critical
```

## 実行例

### Staging Deploy

```bash
# Claude Code内で
/deploy

# または明示的に指定
/deploy staging
```

**期待される出力**:

```
🚀 DeploymentAgent - Staging Deploy

1. Pre-deployment Checks
   ✅ TypeScript: 0 errors
   ✅ Tests: 6/6 passed
   ✅ Build: Success

2. Firebase Deploy
   ✅ Deploying to staging...
   ✅ Deploy complete!

3. Health Check
   ✅ GET https://your-app-staging.web.app/health
   ✅ Status: 200 OK

✅ Deployment Successful
環境: staging
バージョン: v1.2.3
URL: https://your-app-staging.web.app
Duration: 2m 34s
```

### Production Deploy

```bash
/deploy production
```

**期待される出力**:

```
⚠️  Production Deploy Warning

環境: production
バージョン: v1.2.3
前回デプロイ: v1.2.2 (2 days ago)
影響: 本番環境のすべてのユーザー

続行しますか? (yes/no): yes

🚀 DeploymentAgent - Production Deploy

1. Pre-deployment Checks
   ✅ TypeScript: 0 errors
   ✅ Tests: 6/6 passed
   ✅ Build: Success

2. Firebase Deploy
   ✅ Deploying to production...
   ✅ Deploy complete!

3. Health Check
   ✅ GET https://your-app.web.app/health
   ✅ Status: 200 OK

4. Post-Deployment Monitoring
   ⏳ Monitoring for 5 minutes...
   ✅ No errors detected

✅ Production Deployment Successful
環境: production
バージョン: v1.2.3
URL: https://your-app.web.app
Duration: 7m 12s

📊 Deployment Report: .ai/logs/deployment-2025-10-08.md
```

## デプロイレポート

デプロイ完了後、`.ai/logs/deployment-YYYY-MM-DD.md` に詳細レポートが生成されます:

```markdown
# Deployment Report - 2025-10-08

## Summary

- **Environment**: production
- **Version**: v1.2.3
- **Status**: ✅ Success
- **Duration**: 7m 12s
- **Deployed By**: DeploymentAgent
- **Timestamp**: 2025-10-08T10:30:00Z

## Pre-Deployment Checks

- TypeScript: ✅ 0 errors
- Tests: ✅ 6/6 passed
- Build: ✅ Success (234ms)

## Deployment Details

- Target: Firebase Hosting
- Project ID: your-firebase-project-id
- Deploy Time: 2m 15s

## Health Check

- URL: https://your-app.web.app/health
- Status: 200 OK
- Response Time: 123ms

## Metrics

- Build Size: 2.4 MB
- Gzip Size: 512 KB
- Files Deployed: 24

## Rollback Command

```bash
firebase hosting:rollback --site your-app-production
```
```

## トラブルシューティング

### Q1: Firebase CLIが見つからない

```bash
npm install -g firebase-tools
firebase login
```

### Q2: デプロイ権限エラー

```bash
# Firebase Console で権限確認
# Project Settings → Users and permissions
# Deploy権限が必要
```

### Q3: Health Checkが常に失敗する

```typescript
// /health エンドポイントが実装されているか確認
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});
```

## 関連ドキュメント

- [DEPLOYMENT.md](../../DEPLOYMENT.md) - デプロイガイド全体
- [Firebase Documentation](https://firebase.google.com/docs/hosting)
- [docs/AGENT_OPERATIONS_MANUAL.md](../../docs/AGENT_OPERATIONS_MANUAL.md) - DeploymentAgent仕様

---

🤖 このコマンドはDeploymentAgentによって実行されます。
