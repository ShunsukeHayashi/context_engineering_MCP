---
description: セキュリティ脆弱性スキャン実行
---

# Security Scan Command

コードベースのセキュリティ脆弱性を自動スキャンし、レポートを生成します。

## 使用方法

```bash
/security-scan [target]
```

## パラメータ

- `target` (オプション): スキャン対象
  - `all` (デフォルト): 全スキャン実行
  - `dependencies`: 依存関係のみ
  - `code`: ソースコードのみ
  - `secrets`: シークレット検出のみ

## 実行内容

### 1. 依存関係スキャン (npm audit)

```bash
npm audit --json
```

検出される脆弱性:

- **Critical**: 重大な脆弱性（即座に修正必要）
- **High**: 高リスク脆弱性
- **Moderate**: 中リスク脆弱性
- **Low**: 低リスク脆弱性

### 2. ソースコードスキャン (ESLint Security Plugin)

```bash
npx eslint . --ext .ts,.js,.tsx,.jsx \
  --plugin security \
  --rule 'security/*: error'
```

検出される問題:

- SQL Injection 脆弱性
- XSS (Cross-Site Scripting) 脆弱性
- Path Traversal 脆弱性
- 危険な正規表現 (ReDoS)
- 安全でない乱数生成
- eval() の使用

### 3. シークレット検出 (git-secrets)

```bash
git secrets --scan
```

検出される情報:

- API Keys
- パスワード
- アクセストークン
- プライベートキー
- AWS Credentials

### 4. TypeScript型安全性チェック

```bash
npm run typecheck
```

型安全性に関する問題を検出。

## スキャンレポート

スキャン完了後、`.ai/security/scan-YYYY-MM-DD.md` にレポートが生成されます:

### レポート例

```markdown
# Security Scan Report - 2025-10-08

**Scan Time**: 2025-10-08T10:30:00Z
**Duration**: 45 seconds
**Status**: ⚠️ Issues Found

---

## 📊 Summary

| Category | Critical | High | Moderate | Low | Total |
|----------|----------|------|----------|-----|-------|
| Dependencies | 0 | 2 | 3 | 5 | 10 |
| Code | 0 | 1 | 0 | 2 | 3 |
| Secrets | 0 | 0 | 0 | 0 | 0 |
| **Total** | **0** | **3** | **3** | **7** | **13** |

**Overall Score**: 72/100 ⚠️ (Threshold: 80)

---

## 🚨 Critical Issues (0)

None found ✅

---

## 🔴 High Severity Issues (3)

### 1. Prototype Pollution in lodash

**Package**: lodash@4.17.15
**Severity**: High
**CWE**: CWE-1321
**CVSS**: 7.4

**Description**:
Versions of lodash prior to 4.17.19 are vulnerable to prototype pollution.

**Affected Locations**:
- node_modules/lodash/lodash.js

**Recommendation**:
```bash
npm update lodash@>=4.17.21
```

**References**:
- https://nvd.nist.gov/vuln/detail/CVE-2020-8203
- https://github.com/lodash/lodash/pull/4874

---

### 2. XSS Vulnerability in User Input Handling

**File**: src/components/UserProfile.tsx:45
**Severity**: High
**CWE**: CWE-79

**Code**:
```typescript
// ❌ Unsafe
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

**Recommendation**:
```typescript
// ✅ Safe
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{
  __html: DOMPurify.sanitize(userInput)
}} />
```

---

## 🟡 Moderate Severity Issues (3)

### 1. Missing Rate Limiting

**File**: src/api/auth.ts:23
**Severity**: Moderate
**CWE**: CWE-307

**Recommendation**:
Implement rate limiting using express-rate-limit:

```typescript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分
  max: 5, // 5回まで
  message: 'Too many login attempts',
});

app.post('/login', limiter, loginHandler);
```

---

## 🟢 Low Severity Issues (7)

### 1. Weak Random Number Generation

**File**: src/utils/token.ts:12
**Severity**: Low

**Code**:
```typescript
// ❌ 予測可能
const token = Math.random().toString(36);
```

**Recommendation**:
```typescript
// ✅ 暗号学的に安全
import crypto from 'crypto';
const token = crypto.randomBytes(32).toString('hex');
```

---

## 🔧 Recommended Actions

### Immediate (Critical/High)

1. **Update lodash**: `npm update lodash@>=4.17.21`
2. **Fix XSS in UserProfile.tsx**: Implement DOMPurify
3. **Add rate limiting**: Install express-rate-limit

### Short-term (Moderate)

4. **Implement CSRF protection**
5. **Add input validation middleware**
6. **Enable security headers**

### Long-term (Low)

7. **Replace Math.random() with crypto.randomBytes()**
8. **Add security.txt file**
9. **Implement Content Security Policy**

---

## 📋 Compliance

- [x] OWASP Top 10 (2021)
- [x] CWE Top 25
- [ ] GDPR データ保護要件
- [ ] SOC 2 Type II

---

## 🔍 Scan Details

**Tools Used**:
- npm audit (v10.2.0)
- ESLint (v8.50.0) + eslint-plugin-security
- git-secrets (v1.3.0)
- TypeScript (v5.2.0)

**Scan Coverage**:
- Files Scanned: 234
- Lines of Code: 12,450
- Dependencies: 258
- Dev Dependencies: 42

---

## 📈 Trend

| Date | Critical | High | Moderate | Low | Score |
|------|----------|------|----------|-----|-------|
| 2025-10-01 | 0 | 5 | 4 | 8 | 68 |
| 2025-10-05 | 0 | 4 | 3 | 7 | 70 |
| 2025-10-08 | 0 | 3 | 3 | 7 | 72 |

**Improvement**: +4 points (5 days)

---

## 🤖 Next Steps

1. Run: `npm audit fix` (自動修正)
2. Review high severity issues
3. Create issues for manual fixes
4. Re-scan after fixes

**Auto-fix Command**:
```bash
npm audit fix --force
/security-scan all
```

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## スコアリングシステム

セキュリティスコアは以下の計算式で算出されます:

```typescript
let score = 100;

// 脆弱性によるペナルティ
score -= vulnerabilities.critical * 40;  // Critical: -40点
score -= vulnerabilities.high * 20;      // High: -20点
score -= vulnerabilities.moderate * 10;  // Moderate: -10点
score -= vulnerabilities.low * 2;        // Low: -2点

// 最低0点
score = Math.max(0, score);
```

**合格ライン**: 80点以上

## 自動修正

多くの脆弱性は自動修正可能です:

```bash
# 依存関係の自動修正
npm audit fix

# 破壊的変更を含む修正
npm audit fix --force

# package-lock.json の更新のみ
npm audit fix --package-lock-only
```

## 実行例

### Example 1: 全スキャン

```bash
/security-scan all
```

**出力**:

```
🔒 Security Scan - Full

1. Dependency Scan (npm audit)
   ⏳ Scanning 258 packages...
   ⚠️  Found 10 vulnerabilities (0 critical, 2 high, 3 moderate, 5 low)

2. Code Scan (ESLint Security)
   ⏳ Scanning 234 files...
   ⚠️  Found 3 issues (0 critical, 1 high, 0 moderate, 2 low)

3. Secret Detection (git-secrets)
   ⏳ Scanning git history...
   ✅ No secrets found

4. Type Safety Check (TypeScript)
   ⏳ Type checking...
   ✅ 0 errors

📊 Overall Score: 72/100 ⚠️

📝 Report: .ai/security/scan-2025-10-08.md

🔧 Recommended Actions:
1. Run: npm audit fix
2. Fix: src/components/UserProfile.tsx:45 (XSS)
3. Add: Rate limiting on /login endpoint

❌ Below threshold (80 required)
🚨 Escalating to: CISO
```

### Example 2: 依存関係のみスキャン

```bash
/security-scan dependencies
```

**出力**:

```
🔒 Security Scan - Dependencies Only

npm audit --json
⏳ Scanning 258 packages...

📊 Results:
- Critical: 0
- High: 2
- Moderate: 3
- Low: 5

🔧 Auto-fixable: 8/10

Run: npm audit fix
```

### Example 3: シークレット検出のみ

```bash
/security-scan secrets
```

**出力**:

```
🔒 Security Scan - Secrets Detection

git-secrets --scan
⏳ Scanning repository...

✅ No secrets found in:
- Committed files
- Git history
- Staged changes

🔐 Security: PASS
```

## CI/CD統合

GitHub Actionsで自動的にセキュリティスキャンを実行:

### .github/workflows/security-scan.yml

```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # 毎週日曜日

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run security scan
        run: |
          npm audit --audit-level=moderate
          npx eslint . --plugin security

      - name: Upload security report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: .ai/security/
```

## エスカレーション

セキュリティスコアが基準未満の場合、自動的にエスカレーションされます:

| スコア | エスカレーション先 | Severity |
|--------|-------------------|----------|
| < 60点 | CTO + CISO | Sev.1-Critical |
| 60-79点 | CISO | Sev.2-High |
| ≥ 80点 | なし | なし |

## ツール設定

### ESLint Security Plugin

```bash
npm install --save-dev eslint-plugin-security
```

### .eslintrc.json

```json
{
  "plugins": ["security"],
  "extends": ["plugin:security/recommended"],
  "rules": {
    "security/detect-object-injection": "error",
    "security/detect-non-literal-regexp": "warn",
    "security/detect-unsafe-regex": "error",
    "security/detect-buffer-noassert": "error",
    "security/detect-eval-with-expression": "error"
  }
}
```

### git-secrets

```bash
# インストール
brew install git-secrets  # macOS
# または
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets && make install

# 初期化
cd your-project
git secrets --install
git secrets --register-aws
```

## トラブルシューティング

### Q1: npm audit で誤検出が多い

```bash
# 特定のパッケージを除外
npm audit --omit=dev

# audit-level を調整
npm audit --audit-level=high
```

### Q2: ESLint Security Plugin が厳しすぎる

```json
// .eslintrc.json
{
  "rules": {
    "security/detect-object-injection": "warn"  // error → warn
  }
}
```

### Q3: スキャンに時間がかかる

```bash
# 並列実行
npm audit & \
npx eslint . --plugin security & \
git secrets --scan & \
wait
```

## 関連ドキュメント

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [npm audit documentation](https://docs.npmjs.com/cli/v9/commands/npm-audit)
- [ESLint Security Plugin](https://github.com/eslint-community/eslint-plugin-security)

---

🔒 定期的なセキュリティスキャンでプロダクトを守りましょう。
