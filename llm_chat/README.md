# LLM Chat 模块

这是一个通用的LLM聊天功能模块，支持OpenAI兼容的API接口，特别适用于阿里云DashScope等服务。

## 功能特性

- 支持OpenAI兼容的API接口
- 灵活的参数配置（模型、温度、base_url等）
- 单轮和多轮对话支持
- 便捷的快速对话函数
- 完整的错误处理
- 类型提示支持

## 安装依赖

```bash
pip install openai
```

## 环境配置

设置API密钥环境变量：

```bash
export DASHSCOPE_API_KEY="your_api_key_here"
```

## 使用方法

### 1. 基础使用

```python
from llm_chat.chat_client import LLMChatClient

# 创建客户端
client = LLMChatClient(
    model="qwen3-coder-plus",
    temperature=0.7
)

# 单轮对话
response = client.simple_chat(
    user_message="你好，请介绍一下Python",
    system_message="You are a helpful assistant."
)
print(response)
```

### 2. 多轮对话

```python
from llm_chat.chat_client import LLMChatClient

client = LLMChatClient()

# 构建对话历史
messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': '什么是机器学习？'},
]

# 第一轮对话
response1 = client.chat(messages)
messages.append({'role': 'assistant', 'content': response1})

# 继续对话
messages.append({'role': 'user', 'content': '请举个例子'})
response2 = client.chat(messages)
```

### 3. 快速对话

```python
from llm_chat.chat_client import quick_chat

# 一行代码完成对话
response = quick_chat(
    user_message="写一个Python函数计算阶乘",
    model="qwen3-coder-plus",
    temperature=0.3
)
print(response)
```

### 4. 自定义参数

```python
from llm_chat.chat_client import create_chat_client

# 创建自定义配置的客户端
client = create_chat_client(
    base_url="https://your-custom-endpoint.com/v1",
    model="your-model-name",
    temperature=0.5,
    max_tokens=1000
)

response = client.simple_chat("Hello!")
```

## API 参考

### LLMChatClient 类

#### 初始化参数

- `api_key` (str, optional): API密钥，默认从环境变量获取
- `base_url` (str): API基础URL，默认为DashScope兼容模式
- `model` (str): 模型名称，默认为"qwen3-coder-plus"
- `temperature` (float): 生成温度，默认0.7
- `max_tokens` (int, optional): 最大生成token数

#### 主要方法

- `chat(messages, **kwargs)`: 发送聊天请求
- `simple_chat(user_message, system_message, **kwargs)`: 简单单轮对话

### 便捷函数

- `create_chat_client(**kwargs)`: 创建聊天客户端
- `quick_chat(user_message, **kwargs)`: 快速单轮对话

## 支持的模型

- qwen3-coder-plus
- qwen-plus
- qwen-turbo
- 其他OpenAI兼容模型

## 错误处理

模块包含完整的错误处理机制：

```python
try:
    response = client.simple_chat("Hello")
except ValueError as e:
    print(f"配置错误: {e}")
except RuntimeError as e:
    print(f"请求失败: {e}")
```

## 示例文件

查看 `example.py` 文件获取更多使用示例，包括：

- 基础使用示例
- 多轮对话示例
- 快速对话示例
- 不同模型使用示例
- 参数调整示例

运行示例：

```bash
cd llm_chat
python example.py
```

## 注意事项

1. 确保设置了正确的API密钥
2. 检查网络连接和API服务可用性
3. 注意API调用的费用和限制
4. 根据需要调整temperature和max_tokens参数