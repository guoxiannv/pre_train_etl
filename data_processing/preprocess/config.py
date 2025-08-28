#!/usr/bin/env python3
"""
配置文件：包含可调整的参数
"""

# 批次大小配置（根据内存情况调整）
BATCH_SIZE = 500  # 可以根据内存情况调整

# 内存配置建议：
# - 内存 < 8GB: 使用 200-300
# - 内存 8-16GB: 使用 300-500  
# - 内存 > 16GB: 使用 500-1000

# 文件大小阈值（超过此大小启用分批处理）
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB

# 进度显示频率
PROGRESS_DISPLAY_INTERVAL = 5  # 每处理多少个批次显示一次进度

# 输出目录配置
OUTPUT_DIR = "../code_data/cleaned_data"
BACKUP_DIR = "../code_data/cleaned_data"

# 日志配置
VERBOSE_LOGGING = True  # 是否显示详细日志
SHOW_ERROR_DETAILS = True  # 是否显示详细错误信息 