#!/bin/bash

echo "🧠 Context Engineering システムを起動中..."

# 依存関係をインストール
echo "📦 依存関係をインストール中..."
pip install -r ../requirements.txt

# 環境変数をチェック
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY環境変数が設定されていません"
    echo "   .envファイルまたは環境変数でGEMINI_API_KEYを設定してください"
    exit 1
fi

echo "✅ 環境変数確認完了"

# テンプレートディレクトリを作成
mkdir -p templates

echo "🌐 Context Engineering API サーバーを起動中..."
echo ""
echo "📍 アクセス方法:"
echo "   - ダッシュボード: http://localhost:9001"
echo "   - API ドキュメント: http://localhost:9001/docs"
echo "   - WebSocket: ws://localhost:9001/ws"
echo ""
echo "🔧 利用可能な機能:"
echo "   ✨ コンテキスト分析・最適化"
echo "   📋 プロンプトテンプレート管理"
echo "   🎨 マルチモーダル対応"
echo "   🔗 RAG統合"
echo "   📊 リアルタイム可視化"
echo ""

python ../context_engineering/context_api.py