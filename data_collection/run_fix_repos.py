#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复脚本 - 修复newArktsRepos目录中的不完整仓库
"""

from fix_incomplete_repos import scan_and_fix_repos
import os

def main():
    # 设置仓库目录路径
    repos_path = "./newArktsRepos"
    
    # 检查目录是否存在
    if not os.path.exists(repos_path):
        print(f"错误: 目录 {repos_path} 不存在")
        print("请确保已经运行过下载脚本")
        return
    
    print("开始修复newArktsRepos目录中的不完整仓库...")
    print("="*50)
    
    # 运行修复
    try:
        stats, fix_log = scan_and_fix_repos(repos_path, "fix_repos_log.json")
        
        print("\n" + "="*50)
        print("修复总结:")
        print(f"  总仓库数: {stats['total']}")
        print(f"  完整仓库: {stats['complete']}")
        print(f"  不完整仓库: {stats['incomplete']}")
        print(f"  成功修复: {stats['fixed']}")
        print(f"  修复失败: {stats['fix_failed']}")
        
        if stats['fix_failed'] > 0:
            print(f"\n注意: 有 {stats['fix_failed']} 个仓库修复失败")
            print("详细信息请查看 fix_repos_log.json 文件")
        
        if stats['fixed'] > 0:
            print(f"\n✅ 成功修复了 {stats['fixed']} 个仓库!")
        else:
            print("\n✅ 所有仓库都是完整的，无需修复!")
            
    except Exception as e:
        print(f"修复过程中出现错误: {e}")
        return

if __name__ == "__main__":
    main()