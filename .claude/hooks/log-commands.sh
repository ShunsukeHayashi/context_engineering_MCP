#!/bin/bash
# log-commands.sh - Claude Code コマンドログ記録（LDD準拠）
#
# Usage: Claude Code hooks設定に追加
# {
#   "hooks": {
#     "userPromptSubmit": ".claude/hooks/log-commands.sh"
#   }
# }

set -e

# ログディレクトリ作成
LOG_DIR=".ai/logs"
mkdir -p "$LOG_DIR"

# 今日の日付でログファイル
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).md"

# ログファイルが存在しない場合、ヘッダー作成
if [ ! -f "$LOG_FILE" ]; then
  cat > "$LOG_FILE" << EOF
# Log-Driven Development Log - $(date +%Y-%m-%d)

**Device**: ${DEVICE_IDENTIFIER:-$(hostname)}
**Project**: Autonomous-Operations
**Date**: $(date +%Y-%m-%d)

---

## codex_prompt_chain

**intent**:
**plan**:
**implementation**:
**verification**:

## tool_invocations

EOF
fi

# コマンド実行記録を追加
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
WORKDIR=$(pwd)

cat >> "$LOG_FILE" << EOF

### [$TIMESTAMP]
- **command**: \`$1\`
- **workdir**: \`$WORKDIR\`
- **status**: running
- **notes**: Command executed via Claude Code

EOF

echo "✅ Logged to $LOG_FILE"
