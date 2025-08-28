#!/usr/bin/env python3
"""
内存监控脚本：显示当前内存使用情况
"""

import psutil
import os

def get_memory_info():
    """获取内存信息"""
    memory = psutil.virtual_memory()
    
    print("💾 系统内存信息:")
    print(f"   总内存: {memory.total / (1024**3):.2f} GB")
    print(f"   可用内存: {memory.available / (1024**3):.2f} GB")
    print(f"   已使用: {memory.used / (1024**3):.2f} GB")
    print(f"   使用率: {memory.percent:.1f}%")
    
    # 根据可用内存推荐批次大小
    available_gb = memory.available / (1024**3)
    
    if available_gb < 2:
        recommended_batch = 100
        memory_level = "低"
    elif available_gb < 4:
        recommended_batch = 200
        memory_level = "较低"
    elif available_gb < 8:
        recommended_batch = 300
        memory_level = "中等"
    elif available_gb < 16:
        recommended_batch = 500
        memory_level = "较高"
    else:
        recommended_batch = 800
        memory_level = "高"
    
    print(f"\n📊 内存评估: {memory_level}")
    print(f"💡 推荐批次大小: {recommended_batch} 条记录")
    
    if memory_level in ["低", "较低"]:
        print("⚠️  警告: 内存不足，建议:")
        print("   1. 关闭其他应用程序")
        print("   2. 使用更小的批次大小")
        print("   3. 分批处理文件")
    
    return recommended_batch

def get_process_memory():
    """获取当前进程内存使用"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    print(f"\n🔍 当前进程内存使用:")
    print(f"   RSS (物理内存): {memory_info.rss / (1024**2):.2f} MB")
    print(f"   VMS (虚拟内存): {memory_info.vms / (1024**2):.2f} MB")

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 内存使用情况检查")
    print("=" * 60)
    
    try:
        # 获取系统内存信息
        recommended_batch = get_memory_info()
        
        # 获取进程内存信息
        get_process_memory()
        
        print(f"\n" + "=" * 60)
        print("📝 配置建议:")
        print("=" * 60)
        
        # 生成配置文件内容
        config_content = f"""# 根据当前内存情况推荐的配置
BATCH_SIZE = {recommended_batch}  # 批次大小

# 如果仍然内存不足，可以进一步减小批次大小
# 建议范围: {max(50, recommended_batch//2)} - {recommended_batch}

# 其他配置
LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 50MB (降低阈值)
PROGRESS_DISPLAY_INTERVAL = 3  # 更频繁的进度显示
VERBOSE_LOGGING = True
SHOW_ERROR_DETAILS = True
"""
        
        print(config_content)
        
        # 询问是否要更新配置文件
        print("💾 是否要更新配置文件? (y/n): ", end="")
        try:
            user_input = input().strip().lower()
            if user_input in ['y', 'yes', '是']:
                config_file = "config.py"
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write(config_content)
                print(f"✅ 配置文件已更新: {config_file}")
            else:
                print("ℹ️  配置文件未更新")
        except KeyboardInterrupt:
            print("\nℹ️  配置文件未更新")
        
    except Exception as e:
        print(f"❌ 获取内存信息失败: {e}")
        print("💡 请确保已安装 psutil 包: pip install psutil")

if __name__ == "__main__":
    main() 