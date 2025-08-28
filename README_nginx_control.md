# Nginx文件系统一键控制工具

## 概述

这是一套完整的nginx文件系统控制工具，可以安全地启用/禁用nginx中的`/files/` location配置，而不会影响其他location和nginx的正常运行。

## 功能特性

- ✅ **一键启用** - 快速启用文件系统访问
- ✅ **一键禁用** - 快速禁用文件系统访问  
- ✅ **状态检查** - 实时查看文件系统状态
- ✅ **安全备份** - 自动备份配置文件
- ✅ **配置验证** - 自动测试nginx配置语法
- ✅ **服务管理** - 支持nginx服务重启
- ✅ **彩色输出** - 友好的用户界面
- ✅ **权限检查** - 自动检查root权限

## 文件说明

| 文件名 | 功能 | 权限要求 |
|--------|------|----------|
| `nginx_filesystem_control.sh` | 主控制脚本 | 普通用户/root |
| `enable_filesystem.sh` | 启用文件系统 | root |
| `disable_filesystem.sh` | 禁用文件系统 | root |
| `check_filesystem_status.sh` | 状态检查 | 普通用户 |
| `README_nginx_control.md` | 说明文档 | - |

## 快速开始

### 1. 设置执行权限

```bash
chmod +x *.sh
```

### 2. 检查当前状态

```bash
./nginx_filesystem_control.sh status
```

### 3. 启用文件系统

```bash
sudo ./nginx_filesystem_control.sh enable
```

### 4. 禁用文件系统

```bash
sudo ./nginx_filesystem_control.sh disable
```

## 详细使用方法

### 主控制脚本

```bash
# 显示帮助信息
./nginx_filesystem_control.sh help

# 启用文件系统
sudo ./nginx_filesystem_control.sh enable

# 禁用文件系统  
sudo ./nginx_filesystem_control.sh disable

# 检查状态
./nginx_filesystem_control.sh status

# 重启nginx服务
sudo ./nginx_filesystem_control.sh restart

# 测试配置
sudo ./nginx_filesystem_control.sh test
```

### 单独脚本使用

```bash
# 启用文件系统
sudo ./enable_filesystem.sh

# 禁用文件系统
sudo ./disable_filesystem.sh

# 检查状态
./check_filesystem_status.sh
```

## 工作原理

### 启用文件系统

1. 检查nginx配置文件是否存在
2. 备份当前配置文件
3. 移除`deny all`配置（如果存在）
4. 测试nginx配置语法
5. 重载nginx配置
6. 显示操作结果

### 禁用文件系统

1. 检查nginx配置文件是否存在
2. 备份当前配置文件
3. 在`/files/` location块末尾添加`deny all;`
4. 测试nginx配置语法
5. 重载nginx配置
6. 显示操作结果

### 状态检查

1. 检查nginx服务运行状态
2. 检查`/files/` location配置
3. 验证配置文件语法
4. 检查端口监听状态
5. 显示详细状态信息

## 安全特性

- **自动备份**: 每次操作前自动备份配置文件
- **配置验证**: 操作后自动测试nginx配置语法
- **权限检查**: 敏感操作需要root权限
- **错误恢复**: 配置失败时自动恢复备份
- **日志记录**: 详细的操作日志和错误信息

## 配置要求

### Nginx配置结构

脚本期望的nginx配置结构：

```nginx
server {
    listen 8887;
    
    # 其他location配置...
    
    location /files/ {
        alias /data2/;
        autoindex on;
        # ... 其他配置
    }
    
    # 其他location配置...
}
```

### 系统要求

- Linux系统
- nginx已安装并运行
- bash shell
- root权限（用于启用/禁用操作）

## 故障排除

### 常见问题

1. **权限不足**
   ```bash
   sudo ./nginx_filesystem_control.sh enable
   ```

2. **配置文件不存在**
   - 检查nginx是否已安装
   - 确认配置文件路径

3. **配置语法错误**
   - 运行配置测试: `sudo ./nginx_filesystem_control.sh test`
   - 检查nginx错误日志

4. **服务启动失败**
   - 检查端口占用: `netstat -tlnp | grep 8887`
   - 查看系统日志: `journalctl -u nginx`

### 恢复备份

如果操作失败，可以手动恢复备份：

```bash
# 查找备份文件
ls -la /etc/nginx/nginx.conf.backup.*

# 恢复配置
sudo cp /etc/nginx/nginx.conf.backup.YYYYMMDD_HHMMSS /etc/nginx/nginx.conf

# 重载nginx
sudo nginx -s reload
```

## 注意事项

⚠️ **重要提醒**:

1. **备份重要**: 操作前会自动备份，但建议手动备份重要配置
2. **权限要求**: 启用/禁用操作需要root权限
3. **服务影响**: 操作过程中nginx会短暂重载，可能影响正在进行的请求
4. **配置依赖**: 脚本依赖特定的nginx配置结构
5. **测试环境**: 建议先在测试环境验证脚本功能

## 版本信息

- **版本**: 1.0.0
- **作者**: Assistant
- **兼容性**: nginx 1.18+
- **测试环境**: CentOS 7+, Ubuntu 18.04+

## 技术支持

如果遇到问题，请：

1. 检查nginx错误日志: `/var/log/nginx/error.log`
2. 运行状态检查: `./nginx_filesystem_control.sh status`
3. 查看系统日志: `journalctl -u nginx`
4. 确认配置文件语法: `nginx -t`

---

**免责声明**: 此工具仅供学习和生产环境使用，使用前请确保了解其工作原理和可能的影响。作者不对使用此工具造成的任何问题承担责任。
