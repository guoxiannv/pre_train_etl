# ArkTS 全数据处理管道

这个目录包含用于处理全部数据（不采样）的ArkTS代码质量检测脚本，支持中断后继续处理。

## 文件说明

- `arkts_full_data_processor.py` - 主处理脚本
- `README.md` - 本说明文件

## 功能特性

- **全数据处理**: 处理输入文件中的所有数据，不进行采样
- **断点续传**: 支持中途中断后继续处理，自动跳过已处理的项目
- **进度跟踪**: 实时保存处理进度和预估剩余时间
- **批量处理**: 分批处理数据，避免内存溢出
- **多副本判断**: 支持多个LLM副本进行一致性判断
- **OpenAI兼容**: 支持OpenAI API和本地vLLM端点

## 使用方法

### 1. 环境准备

设置环境变量：
```bash
export DASHSCOPE_API_KEY="your_api_key_here"
export DASHSCOPE_BASE_URL="your_base_url_here"
```

### 2. 基本使用

```bash
python arkts_full_data_processor.py \
    --input /path/to/your/data.jsonl \
    --out-dir ./output \
    --replicas 2 \
    --model qwen3-coder-480b-a35b-instruct \
    --concurrency 8 \
    --code-field text
```

### 3. 参数说明

- `--input`: 输入JSONL文件路径（必需）
- `--out-dir`: 输出目录（默认: out_full）
- `--replicas`: 每个项目的LLM副本数量（默认: 2）
- `--model`: 模型名称（默认: qwen3-coder-480b-a35b-instruct）
- `--temps`: 温度参数，逗号分隔（默认: 0.1,0.3）
- `--code-field`: 代码字段名（默认: text）
- `--concurrency`: 并发请求数（默认: 8）
- `--batch-size`: 批处理大小（默认: 100）
- `--max-tokens`: 最大响应token数（默认: 512）
- `--timeout`: 请求超时时间（默认: 90秒）

### 4. 输出文件

处理完成后，输出目录将包含：

- `judgements.jsonl` - 所有判断结果的详细记录（同时用于断点续传）
- `summary.csv` - 最终汇总结果

### 5. 断点续传

如果处理过程中被中断，只需重新运行相同的命令，脚本会自动：
- 从 `judgements.jsonl` 文件中读取已处理的项目ID
- 跳过已完成的项目
- 从中断点继续处理

### 6. 自定义提示词

可以在脚本目录下放置 `JUDGE_PROMPT.txt` 文件来自定义提示词模板。文件中使用 `{code}` 作为代码内容的占位符。

## 示例

### 处理大型数据集

```bash
python arkts_full_data_processor.py \
    --input /data/large_arkts_corpus.jsonl \
    --out-dir ./full_processing_results \
    --replicas 3 \
    --concurrency 16 \
    --batch-size 200 \
    --model qwen3-coder-480b-a35b-instruct
```

### 低并发处理（避免API限制）

```bash
python arkts_full_data_processor.py \
    --input /data/corpus.jsonl \
    --out-dir ./results \
    --concurrency 2 \
    --batch-size 50 \
    --timeout 120
```

## 注意事项

1. **API限制**: 根据你的API提供商调整并发数和批大小
2. **磁盘空间**: 确保有足够的磁盘空间存储结果文件
3. **网络稳定性**: 长时间运行需要稳定的网络连接
4. **内存使用**: 批大小会影响内存使用，根据系统配置调整
5. **备份**: 建议定期备份输出目录，特别是长时间运行的任务

## 故障排除

### 常见问题

1. **API错误**: 检查API密钥和端点URL是否正确
2. **内存不足**: 减小batch-size参数
3. **网络超时**: 增加timeout参数
4. **文件权限**: 确保对输出目录有写权限

### 监控进度

可以通过查看 `judgements.jsonl` 文件来监控处理进度：

```bash
# 查看已处理的项目数量
wc -l output/judgements.jsonl

# 查看最新处理的几个项目
tail -5 output/judgements.jsonl
```