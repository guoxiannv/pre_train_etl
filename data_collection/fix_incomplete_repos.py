#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复不完整的Git仓库脚本
用于修复git clone过程中部分成功但工作目录文件缺失的仓库
"""

import os
import subprocess
import json
from pathlib import Path
from tqdm import tqdm

def check_repo_status(repo_path):
    """
    检查仓库状态
    返回: 'complete', 'incomplete', 'invalid', 'empty'
    """
    if not os.path.exists(repo_path):
        return 'empty'
    
    git_dir = os.path.join(repo_path, '.git')
    if not os.path.exists(git_dir):
        return 'invalid'
    
    # 检查是否有工作目录文件（除了.git目录）
    files = [f for f in os.listdir(repo_path) if f != '.git']
    if not files:
        return 'incomplete'
    
    return 'complete'

def fix_incomplete_repo(repo_path):
    """
    修复不完整的仓库
    返回: (success: bool, message: str)
    """
    try:
        # 切换到仓库目录
        original_cwd = os.getcwd()
        os.chdir(repo_path)
        
        # 检查是否有提交记录
        result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            os.chdir(original_cwd)
            return False, "没有提交记录"
        
        # 恢复工作目录文件
        result = subprocess.run(['git', 'checkout', 'HEAD', '--', '.'], 
                              capture_output=True, text=True)
        
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            return True, "修复成功"
        else:
            return False, f"修复失败: {result.stderr}"
            
    except Exception as e:
        if 'original_cwd' in locals():
            os.chdir(original_cwd)
        return False, f"修复过程出错: {str(e)}"

def scan_and_fix_repos(repos_base_path, fix_log_file="fix_repos.json"):
    """
    扫描并修复所有不完整的仓库
    """
    repos_base_path = Path(repos_base_path)
    
    if not repos_base_path.exists():
        print(f"错误: 路径 {repos_base_path} 不存在")
        return
    
    # 获取所有仓库目录
    repo_dirs = [d for d in repos_base_path.iterdir() if d.is_dir()]
    
    print(f"扫描到 {len(repo_dirs)} 个仓库目录")
    
    # 统计信息
    stats = {
        'total': len(repo_dirs),
        'complete': 0,
        'incomplete': 0,
        'invalid': 0,
        'empty': 0,
        'fixed': 0,
        'fix_failed': 0
    }
    
    # 修复记录
    fix_log = {
        'scan_time': str(Path().cwd()),
        'base_path': str(repos_base_path),
        'incomplete_repos': [],
        'fixed_repos': [],
        'failed_fixes': []
    }
    
    print("\n开始扫描仓库状态...")
    
    # 扫描所有仓库
    for repo_dir in tqdm(repo_dirs, desc="扫描仓库"):
        status = check_repo_status(repo_dir)
        stats[status] += 1
        
        if status == 'incomplete':
            repo_info = {
                'name': repo_dir.name,
                'path': str(repo_dir),
                'status': status
            }
            fix_log['incomplete_repos'].append(repo_info)
    
    print(f"\n扫描结果:")
    print(f"  完整仓库: {stats['complete']}")
    print(f"  不完整仓库: {stats['incomplete']}")
    print(f"  无效仓库: {stats['invalid']}")
    print(f"  空目录: {stats['empty']}")
    
    if stats['incomplete'] == 0:
        print("\n没有发现需要修复的仓库！")
        return
    
    print(f"\n开始修复 {stats['incomplete']} 个不完整的仓库...")
    
    # 修复不完整的仓库
    for repo_info in tqdm(fix_log['incomplete_repos'], desc="修复仓库"):
        repo_path = repo_info['path']
        success, message = fix_incomplete_repo(repo_path)
        
        repo_info['fix_result'] = {
            'success': success,
            'message': message
        }
        
        if success:
            stats['fixed'] += 1
            fix_log['fixed_repos'].append(repo_info)
        else:
            stats['fix_failed'] += 1
            fix_log['failed_fixes'].append(repo_info)
    
    # 保存修复日志
    with open(fix_log_file, 'w', encoding='utf-8') as f:
        json.dump(fix_log, f, ensure_ascii=False, indent=2)
    
    print(f"\n修复完成!")
    print(f"  成功修复: {stats['fixed']}")
    print(f"  修复失败: {stats['fix_failed']}")
    print(f"  修复日志已保存到: {fix_log_file}")
    
    return stats, fix_log

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='修复不完整的Git仓库')
    parser.add_argument('repos_path', help='仓库根目录路径')
    parser.add_argument('--log-file', default='fix_repos.json', 
                       help='修复日志文件名 (默认: fix_repos.json)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='只扫描不修复')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("干运行模式: 只扫描，不进行修复")
        # 这里可以添加只扫描的逻辑
        repos_base_path = Path(args.repos_path)
        repo_dirs = [d for d in repos_base_path.iterdir() if d.is_dir()]
        
        incomplete_count = 0
        for repo_dir in tqdm(repo_dirs, desc="扫描仓库"):
            status = check_repo_status(repo_dir)
            if status == 'incomplete':
                incomplete_count += 1
                print(f"不完整仓库: {repo_dir.name}")
        
        print(f"\n发现 {incomplete_count} 个不完整的仓库")
    else:
        scan_and_fix_repos(args.repos_path, args.log_file)

if __name__ == "__main__":
    main()