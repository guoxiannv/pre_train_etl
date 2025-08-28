# Data Processing Pipeline

这个pipeline用于处理`judgements.jsonl`文件，包含数据分离、泄露检测、token统计等步骤。

## 功能特性

### 🚀 完整的处理流程
1. **数据分离** - 根据decision字段分离数据，移除item_id
2. **泄露检测** - 使用`remove_leaked.py`中的逻辑检测数据泄露
3. **Token统计** - 使用`calculate_tokens.py`统计每行的token数量
4. **数据分割** - 根据泄露标记创建train/test split
5. **扩展预留** - 为未来的pipeline步骤预留空间

### 🔧 可复用组件
- `tag_llm_judgements_with_leaks()` - 从`remove_leaked.py`抽取的泄露检测函数
- 输入：`List[Dict[str, Any]]` 和 `leaked_set_norm: set`
- 输出：添加了`leaked: bool`字段的`List[Dict[str, Any]]`

### 📁 输出文件
- `judgements.jsonl` - 处理后的原始数据（移除item_id，按project_name排序）
- `removed_judgements.jsonl` - 标记为REMOVE的数据
- `kept_with_tag_judgements.jsonl` - 标记为KEEP_WITH_TAG的数据
- `kept_all_judgements.jsonl` - 所有保留的数据（KEEP + KEEP_WITH_TAG）
- `kept_all_leaked_tagged.jsonl` - 添加了leaked字段的数据
- `kept_all_final.jsonl` - 包含leaked和text_tokens字段的数据
- `kept_all_with_split.jsonl` - 最终结果，包含split字段，train数据在前，test数据在后

## 使用方法

### 1. 直接运行pipeline
```bash
cd data_processing/code_data/tagged_data
python format_outrounds.py
```

### 2. 在其他脚本中使用
```python
from format_outrounds import DataProcessingPipeline

# 创建pipeline实例
pipeline = DataProcessingPipeline("/path/to/workspace/root")

# 运行完整pipeline
final_data = pipeline.run_pipeline()

# 或者运行单个步骤
separated_data = pipeline.step1_separate_data()
leaked_data = pipeline.step2_detect_leaks(separated_data['kept_all'])
final_data = pipeline.step3_count_tokens(leaked_data)
```

### 3. 测试pipeline
```bash
cd data_processing/code_data/tagged_data
python test_pipeline.py
```

## Pipeline步骤详解

### Step 1: 数据分离 (`step1_separate_data`)
- 读取`out_rounds/judgements.jsonl`
- 移除`item_id`字段
- 按`project_name`排序
- 根据`decision`字段分离数据

### Step 2: 泄露检测 (`step2_detect_leaks`)
- 加载泄露仓库列表
- 为每个条目添加`leaked: bool`字段
- 使用路径匹配算法检测泄露

### Step 3: Token统计 (`step3_count_tokens`)
- 使用Qwen2.5-Coder-7B tokenizer
- 为每个条目添加`text_tokens: int`字段
- 统计总token数和平均值

### Step 4: 数据分割 (`step4_make_split`)
- 根据`leaked`字段将数据分为train和test两个split
- 为每个条目添加`split: str`字段（'train' 或 'test'）
- 重新组织数据：train数据在前，test数据在后
- 计算并显示每个split的token统计信息
- 输出最终的分割数据文件

## 依赖要求

- `transformers` - 用于加载tokenizer
- `tqdm` - 进度条显示
- `pathlib` - 路径处理
- 自定义模块：
  - `utils.py` - 基础工具函数
  - `remove_leaked.py` - 泄露检测逻辑
  - `calculate_tokens.py` - token统计功能

## 配置说明

### 代理设置
pipeline会自动配置代理环境变量：
- `HTTP_PROXY=http://127.0.0.1:10809`
- `HTTPS_PROXY=http://127.0.0.1:10809`

### 路径配置
所有路径都是相对于workspace root的相对路径，pipeline会自动处理路径转换。

## 错误处理

- 如果泄露检测文件不存在，所有条目会被标记为非泄露
- 如果token统计失败，会返回原始数据
- 每个步骤都有详细的错误日志和异常处理

## 扩展指南

要添加新的pipeline步骤：

1. 在`DataProcessingPipeline`类中添加新的方法
2. 在`run_pipeline`方法中调用新步骤
3. 更新输出路径配置
4. 添加相应的测试用例

示例：
```python
def step5_quality_filter(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Step 5: Quality filtering"""
    # 实现质量过滤逻辑
    return filtered_data
```

## 注意事项

- 确保输入文件`out_rounds/judgements.jsonl`存在
- 确保有足够的磁盘空间存储输出文件
- Token统计可能需要较长时间，取决于数据量
- 建议在运行前备份重要数据
