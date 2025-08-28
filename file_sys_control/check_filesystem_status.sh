#!/bin/bash

# Nginx文件系统状态检查脚本
# 作者: Assistant
# 功能: 检查nginx中/files/ location配置的当前状态

NGINX_CONF="/etc/nginx/nginx.conf"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查nginx配置文件是否存在
check_nginx_conf() {
    if [[ ! -f "$NGINX_CONF" ]]; then
        log_error "nginx配置文件不存在: $NGINX_CONF"
        exit 1
    fi
}

# 检查nginx服务状态
check_nginx_service() {
    log_header "=== Nginx服务状态 ==="
    if systemctl is-active --quiet nginx; then
        log_info "✅ Nginx服务正在运行"
        echo "   服务状态: $(systemctl is-active nginx)"
        echo "   启动时间: $(systemctl show -p ActiveEnterTimestamp nginx | cut -d= -f2)"
    else
        log_error "❌ Nginx服务未运行"
        echo "   服务状态: $(systemctl is-active nginx)"
    fi
}

# 检查文件系统配置状态
check_filesystem_config() {
    log_header "=== 文件系统配置状态 ==="
    
    if grep -q "location /files/" "$NGINX_CONF"; then
        log_info "✅ 找到 /files/ location配置"
        
        # 获取location块的详细信息
        local start_line=$(grep -n "location /files/" "$NGINX_CONF" | cut -d: -f1)
        local end_line=$(sed -n "$start_line,\$p" "$NGINX_CONF" | grep -n "^        }" | head -1 | cut -d: -f1)
        end_line=$((start_line + end_line - 1))
        
        echo "   配置位置: 第 $start_line - $end_line 行"
        
        # 检查是否有deny all
        if sed -n "${start_line},${end_line}p" "$NGINX_CONF" | grep -q "deny all"; then
            log_warn "🚫 文件系统已禁用 (包含 deny all)"
            echo "   状态: 已禁用"
            echo "   访问: 被拒绝"
        else
            log_info "✅ 文件系统已启用"
            echo "   状态: 已启用"
            echo "   访问: 允许 (需要认证)"
            
            # 检查认证配置
            if sed -n "${start_line},${end_line}p" "$NGINX_CONF" | grep -q "auth_basic"; then
                echo "   认证: 已启用"
                local auth_file=$(sed -n "${start_line},${end_line}p" "$NGINX_CONF" | grep "auth_basic_user_file" | awk '{print $2}' | tr -d ';')
                if [[ -n "$auth_file" ]]; then
                    echo "   认证文件: $auth_file"
                    if [[ -f "$auth_file" ]]; then
                        echo "   认证文件状态: ✅ 存在"
                    else
                        echo "   认证文件状态: ❌ 不存在"
                    fi
                fi
            else
                echo "   认证: 未配置"
            fi
            
            # 检查目录配置
            local alias_dir=$(sed -n "${start_line},${end_line}p" "$NGINX_CONF" | grep "alias" | awk '{print $2}' | tr -d ';')
            if [[ -n "$alias_dir" ]]; then
                echo "   服务目录: $alias_dir"
                if [[ -d "$alias_dir" ]]; then
                    echo "   目录状态: ✅ 存在"
                    echo "   目录权限: $(ls -ld "$alias_dir" | awk '{print $1, $3, $4}')"
                else
                    echo "   目录状态: ❌ 不存在"
                fi
            fi
        fi
    else
        log_error "❌ 未找到 /files/ location配置"
        echo "   状态: 未配置"
    fi
}

# 检查nginx配置语法
check_nginx_syntax() {
    log_header "=== Nginx配置语法检查 ==="
    if nginx -t > /tmp/nginx_test.log 2>&1; then
        log_info "✅ Nginx配置语法正确"
        echo "   配置测试: 通过"
    else
        log_error "❌ Nginx配置语法错误"
        echo "   配置测试: 失败"
        echo "   错误详情:"
        cat /tmp/nginx_test.log | sed 's/^/   /'
    fi
    rm -f /tmp/nginx_test.log
}

# 检查端口监听状态
check_port_status() {
    log_header "=== 端口监听状态 ==="
    local port=$(grep "listen.*8887" "$NGINX_CONF" | head -1 | awk '{print $2}' | tr -d ';')
    if [[ -n "$port" ]]; then
        echo "   配置端口: $port"
        if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
            log_info "✅ 端口 $port 正在监听"
            echo "   监听状态: 正常"
        else
            log_warn "⚠️  端口 $port 未监听"
            echo "   监听状态: 异常"
        fi
    else
        log_warn "⚠️  未找到端口配置"
    fi
}

# 显示使用说明
show_usage() {
    log_header "=== 使用说明 ==="
    echo "📋 可用脚本:"
    echo "   • enable_filesystem.sh   - 启用文件系统"
    echo "   • disable_filesystem.sh  - 禁用文件系统"
    echo "   • check_filesystem_status.sh - 检查状态 (当前脚本)"
    echo ""
    echo "🔧 使用方法:"
    echo "   sudo ./enable_filesystem.sh    # 启用文件系统"
    echo "   sudo ./disable_filesystem.sh   # 禁用文件系统"
    echo "   ./check_filesystem_status.sh   # 检查状态"
}

# 主函数
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Nginx文件系统状态检查工具${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    # 检查配置文件
    check_nginx_conf
    
    # 检查各项状态
    check_nginx_service
    echo ""
    check_filesystem_config
    echo ""
    check_nginx_syntax
    echo ""
    check_port_status
    echo ""
    show_usage
}

# 运行主函数
main "$@"
