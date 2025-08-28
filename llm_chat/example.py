#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM聊天功能使用示例

本文件展示了如何使用llm_chat模块进行LLM对话
"""

import os
from chat_client import LLMChatClient, create_chat_client, quick_chat


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 方法1: 直接创建客户端
    client = LLMChatClient(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen3-coder-plus",
        temperature=0.7
    )
    
    # 单轮对话
    response = client.simple_chat(
        user_message="请编写一个Python函数 find_prime_numbers，该函数接受一个整数 n 作为参数，并返回一个包含所有小于 n 的质数（素数）的列表。质数是指仅能被1和其自身整除的正整数，如2, 3, 5, 7等。不要输出非代码的内容。",
        system_message="You are a helpful assistant."
    )
    print("LLM回复:", response)
    print()


def example_multi_turn_chat():
    """多轮对话示例"""
    print("=== 多轮对话示例 ===")
    
    client = create_chat_client(
        model="qwen3-coder-plus",
        temperature=0.5
    )
    
    # 构建多轮对话
    messages = [
        {'role': 'system', 'content': 'You are a Python programming expert.'},
        {'role': 'user', 'content': '请解释什么是装饰器？'},
    ]
    
    # 第一轮对话
    response1 = client.chat(messages)
    print("第一轮回复:", response1[:100] + "...")
    
    # 添加LLM回复到对话历史
    messages.append({'role': 'assistant', 'content': response1})
    
    # 第二轮对话
    messages.append({'role': 'user', 'content': '请给一个装饰器的具体例子'})
    response2 = client.chat(messages)
    print("第二轮回复:", response2[:100] + "...")
    print()


def example_quick_chat():
    """快速对话示例"""
    print("=== 快速对话示例 ===")
    
    # 使用便捷函数进行快速对话
    response = quick_chat(
        user_message="用Python写一个计算斐波那契数列的函数",
        system_message="You are a coding assistant. Only provide code without explanations.",
        model="qwen3-coder-plus",
        temperature=0.3
    )
    print("快速对话回复:", response)
    print()


def example_different_models():
    """不同模型使用示例"""
    print("=== 不同模型使用示例 ===")
    
    client = create_chat_client()
    
    # 使用不同的模型进行对话
    models = ["qwen3-coder-plus", "qwen-plus", "qwen-turbo"]
    
    for model in models:
        try:
            response = client.simple_chat(
                user_message="Hello, what's your name?",
                model=model,
                temperature=0.1
            )
            print(f"模型 {model} 回复: {response[:50]}...")
        except Exception as e:
            print(f"模型 {model} 调用失败: {e}")
    print()


def example_with_parameters():
    """参数调整示例"""
    print("=== 参数调整示例 ===")
    
    client = create_chat_client()
    
    # 测试不同的temperature值
    temperatures = [0.1, 0.5, 0.9]
    user_message = "写一首关于春天的诗"
    
    for temp in temperatures:
        response = client.simple_chat(
            user_message=user_message,
            temperature=temp,
            max_tokens=100
        )
        print(f"Temperature {temp}: {response[:80]}...")
    print()


if __name__ == "__main__":
    # 检查API密钥
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("警告: 未设置DASHSCOPE_API_KEY环境变量")
        print("请设置环境变量: export DASHSCOPE_API_KEY=your_api_key")
        exit(1)
    
    try:
        # 运行所有示例
        # example_basic_usage()
        # example_multi_turn_chat()
        example_quick_chat()
        # example_different_models()
        # example_with_parameters()
        
    except Exception as e:
        print(f"示例运行出错: {e}")
        print("请检查API密钥和网络连接")