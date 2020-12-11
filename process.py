import os
from shutil import rmtree

min_file = 10
related_datasets_path = os.path.curdir + "/related_datasets"
related_normal_path = related_datasets_path + "/normal"
related_translated_path = related_datasets_path + "/translated"

user_datasets_path = os.path.curdir + "/user_datasets"
user_normal_path = user_datasets_path + "/normal"
user_translated_path = user_datasets_path + "/translated"
# 移除图片少的标签
def rm_less_tags(pathname: str) -> None:
    ls_dir = [d for d in os.listdir(pathname) if os.path.isdir(os.path.join(pathname, d))]
    for d in ls_dir:
        path = os.path.join(pathname, d)
        size = len(os.listdir(path))
        if size < min_file:
            rmtree(path)

def merge_tags(pathname1: str, pathname2: str) -> None:
    pass


if __name__ == "__main__":
    rm_less_tags(related_normal_path)
    rm_less_tags(related_translated_path)
    # rm_less_tags(user_translated_path)
    # rm_less_tags(user_normal_path)
