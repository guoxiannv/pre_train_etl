#!/bin/bash

# Nginx文件系统主控制脚本
# 作者: Assistant
# 功能: 一键控制nginx文件系统的启用/禁用/状态检查

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 脚本路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENABLE_SCRIPT="$SCRIPT_DIR/enable_filesystem.sh"
DISABLE_SCRIPT="$SCRIPT_DIR/disable_filesystem.sh"
STATUS_SCRIPT="$SCRIPT_DIR/check_filesystem_status.sh"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}  Nginx文件系统控制工具${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""
    echo -e "${YELLOW}使用方法:${NC}"
    echo "  $0 [选项]"
    echo ""
    echo -e "${YELLOW}选项:${NC}"
    echo "  enable    启用文件系统"
    echo "  disable   禁用文件系统"
    echo "  status    检查当前状态"
    echo "  restart   重启nginx服务"
    echo "  test      测试nginx配置"
    echo "  help      显示此帮助信息"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 enable      # 启用文件系统"
    echo "  $0 disable     # 禁用文件系统"
    echo "  $0 status      # 检查状态"
    echo "  $0 restart     # 重启nginx"
    echo ""
    echo -e "${YELLOW}注意事项:${NC}"
    echo "  • 启用/禁用操作需要root权限"
    echo "  • 所有操作都会自动备份配置文件"
    echo "  • 操作完成后会自动重载nginx配置"
}

# 检查脚本是否存在
check_scripts() {
    local missing_scripts=()
    
    if [[ ! -f "$ENABLE_SCRIPT" ]]; then
        missing_scripts+=("enable_filesystem.sh")
    fi
    
    if [[ ! -f "$DISABLE_SCRIPT" ]]; then
        missing_scripts+=("disable_filesystem.sh")
    fi
    
    if [[ ! -f "$STATUS_SCRIPT" ]]; then
        missing_scripts+=("check_filesystem_status.sh")
    fi
    
    if [[ ${#missing_scripts[@]} -gt 0 ]]; then
        log_error "缺少以下脚本文件:"
        for script in "${missing_scripts[@]}"; do
            echo "   • $script"
        done
        echo ""
        log_error "请确保所有脚本文件都在同一目录下"
        exit 1
    fi
}

# 启用文件系统
enable_filesystem() {
    log_header "正在启用文件系统..."
    if [[ $EUID -ne 0 ]]; then
        log_error "启用操作需要root权限，请使用: sudo $0 enable"
        exit 1
    fi
    
    if [[ -x "$ENABLE_SCRIPT" ]]; then
        "$ENABLE_SCRIPT"
    else
        log_error "启用脚本没有执行权限"
        chmod +x "$ENABLE_SCRIPT"
        "$ENABLE_SCRIPT"
    fi
}

# 禁用文件系统
disable_filesystem() {
    log_header "正在禁用文件系统..."
    if [[ $EUID -ne 0 ]]; then
        log_error "禁用操作需要root权限，请使用: sudo $0 disable"
        exit 1
    fi
    
    if [[ -x "$DISABLE_SCRIPT" ]]; then
        "$DISABLE_SCRIPT"
    else
        log_error "禁用脚本没有执行权限"
        chmod +x "$DISABLE_SCRIPT"
        "$DISABLE_SCRIPT"
    fi
}

# 检查状态
check_status() {
    log_header "正在检查文件系统状态..."
    if [[ -x "$STATUS_SCRIPT" ]]; then
        "$STATUS_SCRIPT"
    else
        log_error "状态检查脚本没有执行权限"
        chmod +x "$STATUS_SCRIPT"
        "$STATUS_SCRIPT"
    fi
}

# 重启nginx服务
restart_nginx() {
    log_header "正在重启nginx服务..."
    if [[ $EUID -ne 0 ]]; then
        log_error "重启操作需要root权限，请使用: sudo $0 restart"
        exit 1
    fi
    
    log_info "停止nginx服务..."
    if systemctl stop nginx; then
        log_info "nginx服务已停止"
    else
        log_warn "停止nginx服务失败"
    fi
    
    log_info "启动nginx服务..."
    if systemctl start nginx; then
        log_info "nginx服务已启动"
        sleep 2
        
        if systemctl is-active --quiet nginx; then
            log_info "✅ nginx服务运行正常"
        else
            log_error "❌ nginx服务启动失败"
            exit 1
        fi
    else
        log_error "启动nginx服务失败"
        exit 1
    fi
}

# 测试nginx配置
test_nginx_config() {
    log_header "正在测试nginx配置..."
    if [[ $EUID -ne 0 ]]; then
        log_error "配置测试需要root权限，请使用: sudo $0 test"
        exit 1
    fi
    
    log_info "测试nginx配置语法..."
    if nginx -t; then
        log_info "✅ nginx配置测试通过"
    else
        log_error "❌ nginx配置测试失败"
        exit 1
    fi
}

# 设置脚本权限
setup_permissions() {
    log_info "设置脚本执行权限..."
    chmod +x "$ENABLE_SCRIPT" 2>/dev/null
    chmod +x "$DISABLE_SCRIPT" 2>/dev/null
    chmod +x "$STATUS_SCRIPT" 2>/dev/null
    chmod +x "$0" 2>/dev/null
    log_info "权限设置完成"
}

# 主函数
main() {
    # 检查脚本文件
    check_scripts
    
    # 设置权限
    setup_permissions
    
    # 检查参数
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi
    
    case "$1" in
        "enable"|"on"|"start")
            enable_filesystem
            ;;
        "disable"|"off"|"stop")
            disable_filesystem
            ;;
        "status"|"check"|"info")
            check_status
            ;;
        "restart"|"reload")
            restart_nginx
            ;;
        "test"|"validate")
            test_nginx_config
            ;;
        "help"|"-h"|"--help"|"-?"|"?")
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
