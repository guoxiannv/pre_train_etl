import requests
import pickle
import os

sys_proxy = os.environ.get('rust_proxy', None)


def get_repo_list_by_api():
    repo_list = []

    for i in range(1, 6):
        # 你的请求 URL 和 access_token
        url = 'https://gitee.com/api/v5/orgs/harmonyos_samples/repos'
        params = {
            'access_token': '8f1941aba9935efd1e645bb1365a6003',
            'type': 'all',
            'page': i,
            'per_page': 100
        }
        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }

        proxies = {
            'http':  sys_proxy,
            'https': sys_proxy,
        }

        # 发起请求
        response = requests.get(url, headers=headers, params=params, proxies=proxies)

        # 检查状态码
        if response.status_code == 200:
            repos = response.json()
            # 打印每个仓库的名称
            for repo in repos:
                repo_list.append(repo["html_url"])
        else:
            print(f'请求失败，状态码：{response.status_code}')
            print(response.text)

    with open("./repo_list.pkl", "wb") as f:
        pickle.dump(repo_list, f)


def download_repo(repo_list, repos_path):
    if not os.path.exists(repos_path):
        os.makedirs(repos_path)
    for repo in repo_list:
        repo_name = repo.split("/")[-1]
        repo_path = os.path.join(repos_path, repo_name)
        if not os.path.exists(repo_path):
            print(f"正在下载 {repo} ...")
            os.system(f"git clone {repo} {repo_path}")
        else:
            print(f"{repo_name} 已存在，跳过下载。")


if __name__ == "__main__":
    with open("./repo_list.pkl", "rb") as f:
        repo_list = pickle.load(f)
    download_repo(repo_list, "./repos")
