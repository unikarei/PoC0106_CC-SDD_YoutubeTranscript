#!/bin/bash

# YouTube文字起こしアプリ 起動スクリプト
# 起動手順.mdに基づく自動起動スクリプト

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトディレクトリ
PROJECT_DIR="/home/ohide/usr8_work/work_23_chatgpt/16_PoCs/0106_cc-sdd"

# ヘルプメッセージ
show_help() {
    echo "使い方: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  --with-frontend    フロントエンドも含めて起動（Dockerで起動）"
    echo "  --frontend-local   フロントエンドをローカルNode.jsで起動"
    echo "  --help            このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0                      # バックエンドのみ起動"
    echo "  $0 --with-frontend      # フロントエンド含めて全て起動（Docker）"
    echo "  $0 --frontend-local     # バックエンド起動後、フロントエンドをローカルで起動"
}

# ログ出力
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Docker Desktopの起動確認
check_docker() {
    log_info "Docker Desktopの起動確認中..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Dockerがインストールされていません"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_warning "Docker Desktopが起動していません"
        
        # WSL環境の場合、Windowsを介してDocker Desktopを起動する
        if grep -qi microsoft /proc/version; then
            log_info "WSL環境を検出しました。Windows側でDocker Desktopを起動します..."
            
            # Windows側でDocker Desktopを起動試行
            if command -v powershell.exe &> /dev/null; then
                log_info "Docker Desktopの起動を試みています..."
                powershell.exe -Command "Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'" 2>/dev/null || true
            fi
        fi
        
        log_info "Docker Desktopの起動を待っています（最大2分）..."
        echo "💡 手動で起動する場合: Windows側でDocker Desktopアプリを起動してください"
        echo ""
        
        # Docker起動を待機（最大120秒 = 60回 × 2秒）
        for i in {1..60}; do
            if docker info &> /dev/null; then
                echo ""
                log_success "Docker Desktopが起動しました"
                return 0
            fi
            echo -n "."
            sleep 2
        done
        
        echo ""
        log_error "Docker Desktopの起動がタイムアウトしました（2分経過）"
        log_error "Windows側でDocker Desktopを手動で起動してから、再度このスクリプトを実行してください"
        exit 1
    fi
    
    log_success "Docker Desktop起動確認完了"
}

# バックエンドサービスの起動
start_backend() {
    log_info "バックエンドサービスを起動中..."
    
    cd "$PROJECT_DIR"
    
    # start_app.shを使用
    if [ -f "./start_app.sh" ]; then
        log_info "./start_app.shを使用してバックエンドを起動"
        ./start_app.sh
    else
        log_warning "start_app.shが見つかりません。docker composeで直接起動します"
        docker compose up -d
    fi
    
    log_success "バックエンドサービスの起動コマンドを実行しました"
}

# サービスの起動確認
check_services() {
    log_info "サービスの起動状態を確認中..."
    
    sleep 5  # サービスが起動するまで少し待つ
    
    cd "$PROJECT_DIR"
    docker compose ps
    
    log_info "ヘルスチェックを実行中..."
    
    # ヘルスチェックの実行（最大30秒待機）
    for i in {1..15}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "バックエンドAPIが正常に起動しました"
            curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    log_warning "ヘルスチェックに応答がありません（起動中の可能性があります）"
}

# フロントエンド（Docker）の起動
start_frontend_docker() {
    log_info "フロントエンドをDockerで起動中..."
    
    cd "$PROJECT_DIR"
    
    if [ -f "./start_app.sh" ]; then
        ./start_app.sh --with-frontend
    else
        log_error "start_app.shが見つかりません"
        exit 1
    fi
    
    log_success "フロントエンドの起動コマンドを実行しました"
}

# フロントエンド（ローカルNode.js）の起動
start_frontend_local() {
    log_info "フロントエンドをローカルNode.jsで起動中..."
    
    cd "$PROJECT_DIR/frontend"
    
    if [ ! -d "node_modules" ]; then
        log_info "node_modulesが見つかりません。npm installを実行します..."
        npm install
    fi
    
    log_info "npm run devを実行します..."
    npm run dev
}

# アクセスURL表示
show_urls() {
    echo ""
    echo "=========================================="
    log_success "起動完了！"
    echo "=========================================="
    echo ""
    echo "🌐 アクセスURL:"
    echo "  - フロントエンド（メインUI）: http://localhost:3000"
    echo "  - バックエンドAPI: http://localhost:8000"
    echo "  - API仕様書（Swagger）: http://localhost:8000/docs"
    echo "  - ヘルスチェック: http://localhost:8000/health"
    echo ""
    echo "🎯 使い方:"
    echo "  1. ブラウザで http://localhost:3000 にアクセス"
    echo "  2. YouTube動画のURLを入力"
    echo "  3. 言語を選択（日本語 or 英語）"
    echo "  4. 「文字起こし開始」ボタンをクリック"
    echo ""
    echo "🛑 停止方法:"
    echo "  - フロントエンド: Ctrl+C"
    echo "  - バックエンド: docker compose down"
    echo ""
}

# メイン処理
main() {
    local with_frontend=false
    local frontend_local=false
    
    # 引数のパース
    while [[ $# -gt 0 ]]; do
        case $1 in
            --with-frontend)
                with_frontend=true
                shift
                ;;
            --frontend-local)
                frontend_local=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "不明なオプション: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "=========================================="
    echo "YouTube文字起こしアプリ 起動スクリプト"
    echo "=========================================="
    echo ""
    
    # Docker確認
    check_docker
    
    # バックエンド起動
    start_backend
    
    # サービス確認
    check_services
    
    # フロントエンド起動（オプションに応じて）
    if [ "$with_frontend" = true ]; then
        start_frontend_docker
    elif [ "$frontend_local" = true ]; then
        show_urls
        start_frontend_local
    else
        show_urls
        log_info "フロントエンドを起動する場合は、以下のコマンドを実行してください："
        echo "  - Dockerで起動: $0 --with-frontend"
        echo "  - ローカルで起動: $0 --frontend-local"
        echo "  - または手動で: cd frontend && npm run dev"
    fi
}

# スクリプト実行
main "$@"
