#!/bin/bash

echo "🚀 ワークフロー管理システムを起動中..."

# 依存関係をインストール
echo "📦 依存関係をインストール中..."
pip install -r ../workflow_system/requirements.txt

# 環境変数をチェック
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY環境変数が設定されていません"
    echo "   .envファイルまたは環境変数でGEMINI_API_KEYを設定してください"
    exit 1
fi

echo "✅ 環境変数確認完了"

# Workflow APIサーバーを起動
echo "🌐 Workflow APIサーバーを起動中..."
echo "   - API: http://localhost:9000"
echo "   - ダッシュボード: http://localhost:9000"
echo "   - WebSocket: ws://localhost:9000/ws"

python ../workflow_system/workflow_api.py