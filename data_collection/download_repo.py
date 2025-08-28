import os
import json
import time
import subprocess
import platform
from datetime import datetime
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from urllib.parse import urlsplit, urlunsplit, quote
from functools import partial
import re

GITEE_USER = os.environ.get("GITEE_USER")
GITEE_TOKEN = os.environ.get("GITEE_TOKEN")
GITHUB_USER = os.environ.get("GITHUB_USER")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def _with_auth(raw_url: str) -> str:
    """
    Return HTTPS URL with basic-auth user:token embedded, if env vars are set.
    Supports github.com and gitee.com.
    """
    parts = urlsplit(raw_url if raw_url.endswith(".git") else raw_url + ".git")
    host = parts.hostname or ""
    user = token = None

    if "github.com" in host and GITHUB_USER and GITHUB_TOKEN:
        user, token = GITHUB_USER, GITHUB_TOKEN
    elif "gitee.com" in host and GITEE_USER and GITEE_TOKEN:
        user, token = GITEE_USER, GITEE_TOKEN

    if user and token and parts.scheme in ("http", "https"):
        # URL-encode to avoid breaking on special chars
        auth = f"{quote(user, safe='')}:{quote(token, safe='')}"
        netloc = f"{auth}@{parts.hostname}"
        if parts.port:
            netloc += f":{parts.port}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

    return raw_url if raw_url.endswith(".git") else raw_url + ".git"

def download_single_repo(repo, repos_path, max_retries=3):
    """Function to download a single repository with retry mechanism"""
    raw_url = repo["git_url"]
    # if not raw_url.endswith(".git"):
    #     raw_url = raw_url + ".git"


    # if "gitee.com" in raw_url:
    #     repo_url = raw_url.replace("https://gitee.com", f"https://{GITEE_USER}:{GITEE_TOKEN}@gitee.com")
    # else:
    #     repo_url = raw_url
    
    repo_url = _with_auth(raw_url)

    safe_author = re.sub(r"[<>:\"/\\|?*\x00-\x1f ]", "_", repo['author'])
    safe_repo_name = re.sub(r"[<>:\"/\\|?*\x00-\x1f ]", "_", repo['repo_name'])
    repo_name = f"{safe_repo_name}~{safe_author}~{repo['id']}"
    repo_path = os.path.join(repos_path, repo_name)
    
    if os.path.exists(repo_path):
        return {
            "repo_name": repo_name,
            "status": "skipped",
            "message": "Repository already exists",
            "repo_info": repo
        }
    
    # Try downloading with retries
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            # Use git clone with timeout and better error handling (cross-platform)
            if platform.system() == "Windows":
                # Windows version using subprocess with timeout
                try:
                    result = subprocess.run(
                        ["git", "clone", "--depth", "1", repo_url, repo_path],
                        timeout=300,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    exit_code = result.returncode
                except subprocess.TimeoutExpired:
                    exit_code = 1
            else:
                # Linux/Mac version using timeout command
                exit_code = os.system(f"timeout 300 git clone --depth 1 {repo_url} {repo_path} 2>/dev/null")
            
            download_time = time.time() - start_time
            
            if exit_code == 0:
                return {
                    "repo_name": repo_name,
                    "status": "downloaded",
                    "message": f"Downloaded successfully in {download_time:.2f}s",
                    "download_time": download_time,
                    "repo_info": repo
                }
            else:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    return {
                        "repo_name": repo_name,
                        "status": "failed",
                        "message": f"Failed after {max_retries} attempts",
                        "error_code": exit_code,
                        "repo_info": repo,
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return {
                    "repo_name": repo_name,
                    "status": "failed",
                    "message": f"Exception: {str(e)}",
                    "repo_info": repo,
                    "timestamp": datetime.now().isoformat()
                }
    
    return {
        "repo_name": repo_name,
        "status": "failed",
        "message": "Unknown error",
        "repo_info": repo,
        "timestamp": datetime.now().isoformat()
    }


def download_repo(repo_list, repos_path, max_workers=None, failed_log_file="failed_repos.json"):
    """Download repository list using multiprocessing with enhanced progress tracking"""
    if not os.path.exists(repos_path):
        os.makedirs(repos_path)
    
    # If max_workers not specified, use CPU core count but limit to reasonable number
    if max_workers is None:
        max_workers = min(cpu_count(), len(repo_list), 8)  # Limit to 8 to avoid overwhelming
    
    print(f"开始下载 {len(repo_list)} 个仓库，使用 {max_workers} 个并行进程...")
    print(f"下载目录: {repos_path}")
    print(f"失败记录文件: {failed_log_file}")
    print("-" * 60)
    
    # Create partial function with fixed repos_path parameter
    download_func = partial(download_single_repo, repos_path=repos_path)
    
    # Statistics counters
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    failed_repos = []
    
    # Use process pool for parallel downloads
    with Pool(processes=max_workers) as pool:
        # Create progress bar with more detailed information
        with tqdm(total=len(repo_list), 
                 desc="下载进度", 
                 unit="repo",
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}") as pbar:
            
            # Use imap to get results as they complete
            for result in pool.imap(download_func, repo_list):
                # Update counters based on result
                if result["status"] == "downloaded":
                    downloaded_count += 1
                    pbar.set_postfix_str(f"✓{downloaded_count} ⏭{skipped_count} ✗{failed_count}")
                elif result["status"] == "skipped":
                    skipped_count += 1
                    pbar.set_postfix_str(f"✓{downloaded_count} ⏭{skipped_count} ✗{failed_count}")
                elif result["status"] == "failed":
                    failed_count += 1
                    failed_repos.append(result)
                    pbar.set_postfix_str(f"✓{downloaded_count} ⏭{skipped_count} ✗{failed_count}")
                
                pbar.update(1)
    
    # Save failed repositories to JSON file
    if failed_repos:
        failed_data = {
            "timestamp": datetime.now().isoformat(),
            "total_failed": len(failed_repos),
            "failed_repositories": failed_repos
        }
        
        with open(failed_log_file, 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n❌ 失败的仓库信息已保存到: {failed_log_file}")
    
    # Print detailed summary
    print("\n" + "="*60)
    print("📊 下载汇总报告:")
    print(f"  ✅ 成功下载: {downloaded_count} 个仓库")
    print(f"  ⏭️  跳过已存在: {skipped_count} 个仓库")
    print(f"  ❌ 下载失败: {failed_count} 个仓库")
    print(f"  📁 总计处理: {len(repo_list)} 个仓库")
    
    if failed_count > 0:
        print(f"\n⚠️  失败率: {failed_count/len(repo_list)*100:.1f}%")
        print("💡 建议检查网络连接或重新运行脚本重试失败的仓库")
    
    print("="*60)
    
    return {
        "downloaded": downloaded_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "failed_repos": failed_repos
    }

if __name__ == "__main__":
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_script_dir, "./arkts_repos.json"), "rb") as f:
        repo_list = json.load(f)

    download_repo(repo_list, "./ArktsRepos", max_workers=4)
    print("Download completed!")
