#!/bin/bash

# ArkTS 全数据处理示例脚本
# 使用前请根据实际情况修改以下参数

# 设置环境变量（请替换为实际的API密钥和端点）
export DASHSCOPE_API_KEY="your_api_key_here"
export DASHSCOPE_BASE_URL="your_base_url_here"

# 输入文件路径（请替换为实际的输入文件）
INPUT_FILE="/path/to/your/data.jsonl"

# 输出目录
OUTPUT_DIR="./full_processing_results"

# 检查输入文件是否存在
if [ ! -f "$INPUT_FILE" ]; then
    echo "错误: 输入文件不存在: $INPUT_FILE"
    echo "请修改 INPUT_FILE 变量为正确的文件路径"
    exit 1
fi

# 检查API密钥是否设置
if [ "$DASHSCOPE_API_KEY" = "your_api_key_here" ]; then
    echo "警告: 请设置正确的 DASHSCOPE_API_KEY"
    echo "请修改脚本中的环境变量设置"
    exit 1
fi

echo "开始处理全数据集..."
echo "输入文件: $INPUT_FILE"
echo "输出目录: $OUTPUT_DIR"
echo "模型: qwen3-coder-480b-a35b-instruct"
echo ""

# 运行处理脚本
python analysis/llm_bad_case_analysis/full_data_processing/arkts_full_data_processor.py \
    --input /home/stefan/Document/PythonProject/pretrain_etl/data_processing/code_data/cleaned_data/test.jsonl \
    --out-dir ./out_rounds \
    --replicas 1 \
    --model /data2/lyh/base_model/Qwen3-Coder-30B-A3B-Instruct \
    --temps 0.1,0.3 \
    --code-field text \
    --concurrency 8 \
    --batch-size 100 \
    --max-tokens 512 \
    --base-url http://localhost:8000/v1 \
    --timeout 90

echo ""
echo "处理完成！结果保存在: $OUTPUT_DIR"
echo "查看汇总结果: cat $OUTPUT_DIR/summary.csv"
echo "查看处理进度: cat $OUTPUT_DIR/progress.json"