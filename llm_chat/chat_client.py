import os
from typing import List, Dict, Optional, Any
from openai import OpenAI


class LLMChatClient:
    """通用LLM聊天客户端，支持OpenAI兼容接口"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen3-coder-plus",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        初始化LLM聊天客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量DASHSCOPE_API_KEY获取
            base_url: API基础URL
            model: 使用的模型名称
            temperature: 生成温度，控制随机性
            max_tokens: 最大生成token数
            **kwargs: 其他OpenAI客户端参数
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("API key is required. Please set DASHSCOPE_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            **kwargs
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式为[{'role': 'user/system/assistant', 'content': '内容'}]
            model: 模型名称，如果为None则使用初始化时的模型
            temperature: 生成温度，如果为None则使用初始化时的温度
            max_tokens: 最大生成token数，如果为None则使用初始化时的设置
            **kwargs: 其他chat.completions.create参数
        
        Returns:
            str: LLM的回复内容
        """
        completion_params = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            **kwargs
        }
        
        if max_tokens is not None or self.max_tokens is not None:
            completion_params["max_tokens"] = max_tokens or self.max_tokens
        
        try:
            completion = self.client.chat.completions.create(**completion_params)
            return completion.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM chat request failed: {str(e)}")
    
    def simple_chat(
        self,
        user_message: str,
        system_message: str = "You are a helpful assistant.",
        **kwargs
    ) -> str:
        """
        简单的单轮对话
        
        Args:
            user_message: 用户消息
            system_message: 系统消息
            **kwargs: 其他chat参数
        
        Returns:
            str: LLM的回复内容
        """
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ]
        return self.chat(messages, **kwargs)


def create_chat_client(
    api_key: Optional[str] = None,
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    model: str = "qwen3-coder-plus",
    **kwargs
) -> LLMChatClient:
    """
    便捷函数：创建LLM聊天客户端
    
    Args:
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
        **kwargs: 其他LLMChatClient参数
    
    Returns:
        LLMChatClient: 聊天客户端实例
    """
    return LLMChatClient(
        api_key=api_key,
        base_url=base_url,
        model=model,
        **kwargs
    )


def quick_chat(
    user_message: str,
    system_message: str = "You are a helpful assistant.",
    api_key: Optional[str] = None,
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    model: str = "qwen3-coder-plus",
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    便捷函数：快速单轮对话
    
    Args:
        user_message: 用户消息
        system_message: 系统消息
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
        temperature: 生成温度
        **kwargs: 其他参数
    
    Returns:
        str: LLM的回复内容
    """
    client = create_chat_client(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        **kwargs
    )
    return client.simple_chat(user_message, system_message)