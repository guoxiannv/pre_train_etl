# 内存优化使用指南

## 问题描述
当处理大型JSONL文件时，可能会遇到 `MemoryError` 错误，这是因为一次性将所有数据加载到内存中导致的。

## 解决方案

### 方案1：自动分批处理（已实现）
- 自动检测文件大小
- 大文件（>100MB）自动启用分批处理
- 小文件使用常规处理

### 方案2：手动配置批次大小
根据你的内存情况调整批次大小：

```python
# 在 pre_process_arkts.py 中修改
BATCH_SIZE = 500  # 根据内存情况调整
```

**内存配置建议：**
- 内存 < 8GB: 使用 200-300
- 内存 8-16GB: 使用 300-500  
- 内存 > 16GB: 使用 500-1000

## 使用步骤

### 步骤1：检查内存情况
```bash
cd data_processing/preprocess
python memory_monitor.py
```

这个脚本会：
- 显示系统内存信息
- 推荐合适的批次大小
- 生成配置文件

### 步骤2：调整配置（可选）
如果内存不足，可以手动调整 `config.py` 中的参数：

```python
# 减小批次大小
BATCH_SIZE = 200  # 从500改为200

# 降低大文件阈值
LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 从100MB改为50MB
```

### 步骤3：运行主脚本
```bash
python pre_process_arkts.py
```

## 监控和调试

### 内存使用监控
脚本运行时会显示：
- 每个文件的处理进度
- 批次处理状态
- 内存使用情况

### 错误处理
- 自动跳过有问题的文件
- 详细的错误信息
- 备份预处理数据

## 性能优化建议

### 1. 关闭其他应用程序
在运行脚本前，关闭不必要的应用程序以释放内存。

### 2. 分批处理大文件
如果单个文件很大，可以手动分割文件：
```bash
# 使用split命令分割大文件
split -l 10000 large_file.jsonl large_file_part_
```

### 3. 使用SSD存储
如果可能，将数据文件放在SSD上，提高读取速度。

### 4. 调整Python内存限制
```bash
# 设置Python内存限制（Linux/Mac）
export PYTHONMALLOC=malloc
export PYTHONDEVMODE=1
```

## 故障排除

### 问题1：仍然内存不足
**解决方案：**
1. 进一步减小批次大小（如100-200）
2. 降低大文件阈值（如30MB）
3. 使用更小的测试文件

### 问题2：处理速度慢
**解决方案：**
1. 增加批次大小（如果内存允许）
2. 减少进度显示频率
3. 关闭详细日志

### 问题3：文件格式错误
**解决方案：**
1. 运行 `debug_file_check.py` 检查文件
2. 修复JSON格式问题
3. 检查文件编码

## 配置文件说明

### config.py
```python
# 批次大小配置
BATCH_SIZE = 500

# 文件大小阈值
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB

# 进度显示频率
PROGRESS_DISPLAY_INTERVAL = 5

# 输出目录
OUTPUT_DIR = "../code_data/cleaned_data"
```

## 联系支持
如果遇到问题，请：
1. 运行 `memory_monitor.py` 检查内存
2. 运行 `debug_file_check.py` 检查文件
3. 查看错误日志信息
4. 根据错误类型调整配置 