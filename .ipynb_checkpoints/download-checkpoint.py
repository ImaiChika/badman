import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 使用国内镜像

from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen-7B-Chat",
    local_dir="./Qwen-7B-Chat",           # 下载到这个文件夹
    local_dir_use_symlinks=False,
    resume_download=True,                 # 支持断点续传
    max_workers=4                         # 多线程加速
)