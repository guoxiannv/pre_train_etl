# 统一文本处理脚本使用说明

## 功能概述

`unified_text_processor.py` 是一个统一的文本处理脚本，合并了 `extract_prompt_text.py` 和 `concatenate_fields.py` 的功能，支持两种不同格式的数据拼接：

1. **Prompt格式**：从 `prompt` 字段中提取三段内容并拼接成 `text` 字段
2. **Fields格式**：将 `above_functions + source_method_code + below_functions` 拼接成 `text` 字段

## 主要特性

- ✅ **自动检测数据类型**：可以自动识别输入数据是prompt格式还是fields格式
- ✅ **批量处理**：支持处理整个目录下的所有JSONL文件
- ✅ **统一输出**：所有处理结果输出到同一个目录
- ✅ **字段标准化**：自动重命名字段（projectName→project_name, filePath/relativePath→path）
- ✅ **ID生成**：基于path生成稳定的SHA256哈希ID
- ✅ **详细统计**：提供完整的处理统计信息

## 使用方法

### 1. 基本用法

```bash
# 处理prompt格式数据目录
python unified_text_processor.py --prompt-dir bg_data --output-dir unified_output

# 处理fields格式数据目录  
python unified_text_processor.py --fields-dir bg_data_select --output-dir unified_output

# 同时处理两种格式的数据
python unified_text_processor.py --prompt-dir bg_data --fields-dir bg_data_select --output-dir unified_output

# 处理单个文件（自动检测类型）
python unified_text_processor.py --single-file test.jsonl --output-dir unified_output
```

### 2. 高级选项

```bash
# 强制指定文件类型
python unified_text_processor.py --prompt-dir bg_data --file-type prompt

# 使用相对路径（相对于脚本所在目录）
python unified_text_processor.py --prompt-dir ./bg_data --fields-dir ./bg_data_select
```

### 3. 目录结构示例

处理前：
```
pretrain_etl/data_processing/preprocess/
├── unified_text_processor.py
├── bg_data/                    # prompt格式数据
│   ├── file1.jsonl
│   └── file2.jsonl
└── bg_data_select/             # fields格式数据
    ├── file3.jsonl
    └── file4.jsonl
```

处理后：
```
pretrain_etl/data_processing/preprocess/
├── unified_text_processor.py
├── unified_output/             # 统一输出目录
│   ├── file1_processed.jsonl
│   ├── file2_processed.jsonl
│   ├── file3_processed.jsonl
│   └── file4_processed.jsonl
```

## 数据格式支持

### Prompt格式输入
```json
{
  "prompt": "The context above the method is:\n```arkts\n...code...\n```\n\nAnd here is the code snippet you are asked to complete:\n```arkts\n...code...\n```\n\nEnsure that only missing codes...",
  "response": "```arkts\n...replacement_code...\n```",
  "repoUrl": "https://github.com/user/repo.git"
}
```

### Fields格式输入
```json
{
  "above_functions": "function above() {...}",
  "source_method_code": "function main() {...}",
  "below_functions": "function below() {...}",
  "projectName": "demo_project",
  "filePath": "src/main.ets"
}
```

### 统一输出格式
```json
{
  "text": "拼接后的完整代码内容",
  "external_imported": "外部导入信息（如果有）",
  "id": "基于path生成的稳定ID",
  "project_name": "标准化后的项目名",
  "path": "标准化后的文件路径",
  "concatenation_status": "处理状态信息"
}
```

## 处理逻辑

### Prompt格式处理
1. 从 `prompt` 字段提取三段代码内容
2. 提取 `external_imported` 信息
3. 替换 `<unused98>` 标签为 `response` 中的代码
4. 标准化字段名和生成ID

### Fields格式处理
1. 智能处理字段值（字符串、列表、字典）
2. 拼接 `above_functions + source_method_code + below_functions`
3. 标准化字段名和生成ID
4. 记录拼接状态

## 统计信息说明

脚本运行完成后会显示详细统计：

```
📊 处理统计信息
📝 Prompt类型数据:
   总记录数: 1500
   成功处理: 1450
   跳过记录: 50
   替换标签: 200
   提取外部: 150

🔗 Fields类型数据:
   总记录数: 800
   成功处理: 750
   跳过记录: 30
   缺少字段: 20

🆔 通用处理:
   生成ID数: 2200
   字段重命名: 500
```

## 注意事项

1. **输入目录结构**：确保输入目录存在且包含有效的JSONL文件
2. **文件格式**：支持 `.jsonl` 和 `.json` 文件
3. **内存使用**：大文件处理时注意内存使用情况
4. **字段完整性**：缺少必要字段的记录会被标记并跳过
5. **错误处理**：JSON解析错误的行会被跳过并记录

## 错误排查

### 常见问题

1. **目录不存在**：检查输入目录路径是否正确
2. **没有找到文件**：确认目录下有 `.jsonl` 或 `.json` 文件
3. **JSON解析失败**：检查文件格式是否正确
4. **字段缺失**：确认输入数据包含必要字段

### 调试建议

1. 先用 `--single-file` 测试单个文件
2. 检查输出的 `processing_status` 和 `concatenation_status` 字段
3. 观察控制台输出的处理日志
