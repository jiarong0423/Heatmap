#!/bin/bash

# ============================================
# 股票資金流向分析 - 自動化執行腳本
# ============================================

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案根目錄（自動偵測）
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 日誌檔案
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/auto_run_$(date +%Y%m%d_%H%M%S).log"

# 確保必要資料夾存在
mkdir -p "$LOG_DIR" "$PROJECT_DIR/out" "$PROJECT_DIR/stock_data"

# ============================================
# 函數：印出帶顏色的訊息
# ============================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================
# 函數：檢查 Python 環境
# ============================================
check_python() {
    log_info "檢查 Python 環境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$($PYTHON_CMD --version)
        log_success "找到 Python: $PYTHON_VERSION"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$($PYTHON_CMD --version)
        log_success "找到 Python: $PYTHON_VERSION"
    else
        log_error "找不到 Python！請先安裝 Python 3.8+"
        exit 1
    fi
}

# ============================================
# 函數：檢查依賴套件
# ============================================
check_dependencies() {
    log_info "檢查依賴套件..."
    
    if [ -f "requirements.txt" ]; then
        log_info "安裝/更新依賴套件..."
        $PYTHON_CMD -m pip install -r requirements.txt --quiet --upgrade
        
        if [ $? -eq 0 ]; then
            log_success "依賴套件安裝完成"
        else
            log_error "依賴套件安裝失敗"
            exit 1
        fi
    else
        log_warning "找不到 requirements.txt"
    fi
}

# ============================================
# 函數：執行 Python 腳本
# ============================================
run_script() {
    local script_name=$1
    local description=$2
    
    log_info "=========================================="
    log_info "執行: $description"
    log_info "=========================================="
    
    if [ ! -f "$script_name" ]; then
        log_error "找不到檔案: $script_name"
        return 1
    fi
    
    $PYTHON_CMD "$script_name" 2>&1 | tee -a "$LOG_FILE"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "$description 執行成功"
        return 0
    else
        log_error "$description 執行失敗"
        return 1
    fi
}

# ============================================
# 函數：開啟結果報告
# ============================================
open_report() {
    log_info "尋找最新報告..."
    
    LATEST_REPORT=$(ls -t "$PROJECT_DIR/out"/*.html 2>/dev/null | head -n 1)
    
    if [ -n "$LATEST_REPORT" ]; then
        log_success "找到報告: $(basename "$LATEST_REPORT")"
        
        # 根據作業系統開啟檔案
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open "$LATEST_REPORT"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open "$LATEST_REPORT"
        else
            log_warning "請手動開啟: $LATEST_REPORT"
        fi
    else
        log_warning "找不到報告檔案"
    fi
}

# ============================================
# 主程式
# ============================================
main() {
    echo ""
    log_info "╔════════════════════════════════════════╗"
    log_info "║   股票資金流向分析 - 自動化執行      ║"
    log_info "║   開始時間: $(date '+%Y-%m-%d %H:%M:%S')    ║"
    log_info "╚════════════════════════════════════════╝"
    echo ""
    
    # 1. 檢查環境
    check_python
    check_dependencies
    
    # 2. 執行資料抓取
    run_script "tw_stock_fetcher.py" "台股數據抓取"
    FETCH_STATUS=$?
    
    # 3. 執行資金流分析
    run_script "sector_flow_tracker.py" "板塊資金流分析"
    TRACKER_STATUS=$?
    
    # 4. 生成熱力圖
    run_script "sector_heatmap.py" "熱力圖生成"
    HEATMAP_STATUS=$?
    
    # 5. 總結報告
    echo ""
    log_info "=========================================="
    log_info "執行總結"
    log_info "=========================================="
    
    [ $FETCH_STATUS -eq 0 ] && log_success "✓ 數據抓取成功" || log_error "✗ 數據抓取失敗"
    [ $TRACKER_STATUS -eq 0 ] && log_success "✓ 資金流分析成功" || log_error "✗ 資金流分析失敗"
    [ $HEATMAP_STATUS -eq 0 ] && log_success "✓ 熱力圖生成成功" || log_error "✗ 熱力圖生成失敗"
    
    echo ""
    log_info "日誌檔案: $LOG_FILE"
    
    # 6. 開啟報告（可選）
    if [ $HEATMAP_STATUS -eq 0 ]; then
        read -p "是否開啟報告？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open_report
        fi
    fi
    
    log_info "完成時間: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# 執行主程式
main
