from typing import Tuple, Callable, Any, Dict
from types import FunctionType
from pixivpy3 import *
import time
from shutil import rmtree
from .constants import MIN_FILES

import os
from .constants import TOTAL_VIEW, TOTAL_BOOKMARKS, ILLEGAL_CHARS


def exception(callback: Callable) -> Callable:
    def wrapper(*args, **kwargs) -> Tuple:
        results = None
        try:
            results = callback(*args, **kwargs)
        except PixivError as e:
            return results, e
        return results, None

    return wrapper


def make_tag_dir(dir_name, path):
    path = os.path.join(path, dir_name)
    if os.path.exists(path):
        return False
    os.mkdir(path)
    return dir_name


# 评分高的图片
def highQualityCallback(value):
    return value.total_view >= TOTAL_VIEW and value.total_bookmarks >= TOTAL_BOOKMARKS and value.type == "illust"


# 评分低的图片
def lowQualityCallback(value):
    return value.total_view < TOTAL_VIEW and value.total_bookmarks < TOTAL_BOOKMARKS and value.type == "illust"
#  标签里面可能有 ABC/dd名称，需要将"/"转化掉
def check_name(pathname: str) -> bool:
    for ic in ILLEGAL_CHARS:
        if pathname.find(ic) != -1:
            return True

    return False


def rename(pathname: str) -> str:
    if check_name(pathname):
        for ic in ILLEGAL_CHARS:
            pathname = pathname.replace(ic, "_")
    return pathname


def is_less(result: list) -> bool:
    if len(result) < 10:
        return True
    return False

# 移除图片少的标签
def rm_less_tags(pathname: str) -> None:
    ls_dir = [d for d in os.listdir(pathname) if os.path.isdir(os.path.join(pathname, d))]
    for d in ls_dir:
        path = os.path.join(pathname, d)
        size = len(os.listdir(path))
        if size < MIN_FILES:
            rmtree(path)
