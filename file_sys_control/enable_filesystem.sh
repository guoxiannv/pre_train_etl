#!/bin/bash

# Nginx文件系统一键启用脚本
# 作者: Assistant
# 功能: 启用nginx中的/files/ location配置

NGINX_CONF="/etc/nginx/nginx.conf"
BACKUP_FILE="/etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"
TEMP_FILE="/tmp/nginx.conf.tmp"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检查nginx配置文件是否存在
check_nginx_conf() {
    if [[ ! -f "$NGINX_CONF" ]]; then
        log_error "nginx配置文件不存在: $NGINX_CONF"
        exit 1
    fi
}

# 备份原配置文件
backup_config() {
    log_info "备份原配置文件到: $BACKUP_FILE"
    cp "$NGINX_CONF" "$BACKUP_FILE"
    if [[ $? -ne 0 ]]; then
        log_error "备份配置文件失败"
        exit 1
    fi
}

# 检查文件系统是否已经启用
check_filesystem_status() {
    if grep -q "location /files/" "$NGINX_CONF"; then
        if sed -n '/location \/files\//,/}/p' "$NGINX_CONF" | grep -q "deny all"; then
            log_info "文件系统当前状态: 已禁用"
            return 1
        else
            log_info "文件系统当前状态: 已启用"
            return 0
        fi
    else
        log_warn "未找到/files/ location配置"
        return 2
    fi
}

# 启用文件系统
enable_filesystem() {
    log_info "正在启用文件系统..."
    
    # 创建临时文件
    cp "$NGINX_CONF" "$TEMP_FILE"
    
    # 查找location /files/的位置
    local start_line=$(grep -n "location /files/" "$TEMP_FILE" | cut -d: -f1)
    if [[ -z "$start_line" ]]; then
        log_error "未找到location /files/配置"
        return 1
    fi
    
    # 查找对应的结束大括号
    local end_line=$(sed -n "$start_line,\$p" "$TEMP_FILE" | grep -n "^        }" | head -1 | cut -d: -f1)
    if [[ -z "$end_line" ]]; then
        log_error "无法找到location /files/的结束位置"
        return 1
    fi
    end_line=$((start_line + end_line - 1))
    
    # 检查是否已经被注释
    if sed -n "${start_line}p" "$TEMP_FILE" | grep -q "^#"; then
        log_info "取消注释location /files/配置..."
        # 取消注释整个location块
        sed -i "${start_line},${end_line}s/^        #/        /" "$TEMP_FILE"
    else
        log_info "location /files/配置已经启用"
    fi
    
    # 检查是否有deny all配置需要移除
    if sed -n "${start_line},${end_line}p" "$TEMP_FILE" | grep -q "deny all"; then
        log_info "移除deny all配置..."
        sed -i "/location \/files\//,/}/s/^        deny all;.*$//" "$TEMP_FILE"
        # 清理空行
        sed -i '/^[[:space:]]*$/d' "$TEMP_FILE"
    fi
    
    # 替换临时文件
    mv "$TEMP_FILE" "$NGINX_CONF"
    
    log_info "文件系统配置已启用"
}

# 测试nginx配置
test_nginx_config() {
    log_info "测试nginx配置..."
    if nginx -t; then
        log_info "nginx配置测试通过"
        return 0
    else
        log_error "nginx配置测试失败"
        return 1
    fi
}

# 重载nginx配置
reload_nginx() {
    log_info "重载nginx配置..."
    if systemctl reload nginx; then
        log_info "nginx配置重载成功"
        return 0
    else
        log_error "nginx配置重载失败"
        return 1
    fi
}

# 显示状态
show_status() {
    log_info "当前文件系统状态:"
    if check_filesystem_status; then
        echo "✅ 文件系统已启用"
        echo "📁 访问路径: http://your-server:8887/files/"
        echo "🔐 需要认证: 是"
    else
        echo "❌ 文件系统已禁用"
        echo "🚫 访问被拒绝"
    fi
}

# 主函数
main() {
    log_info "=== Nginx文件系统启用脚本 ==="
    
    # 检查权限
    check_root
    
    # 检查配置文件
    check_nginx_conf
    
    # 检查当前状态
    local current_status=$(check_filesystem_status)
    if [[ $current_status -eq 0 ]]; then
        log_warn "文件系统已经启用，无需重复操作"
        show_status
        exit 0
    fi
    
    # 备份配置
    backup_config
    
    # 启用文件系统
    enable_filesystem
    
    # 测试配置
    if ! test_nginx_config; then
        log_error "配置测试失败，正在恢复备份..."
        cp "$BACKUP_FILE" "$NGINX_CONF"
        exit 1
    fi
    
    # 重载nginx
    if ! reload_nginx; then
        log_error "nginx重载失败，请手动检查配置"
        exit 1
    fi
    
    log_info "=== 文件系统启用完成 ==="
    show_status
    
    log_info "备份文件位置: $BACKUP_FILE"
    log_info "如需恢复，请运行: cp $BACKUP_FILE $NGINX_CONF && nginx -s reload"
}

# 运行主函数
main "$@"
