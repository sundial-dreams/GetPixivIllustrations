from pixivpy3 import *
import os
from shutil import copyfile, rmtree
from tqdm import trange, tqdm
from queue import Queue

need_get_tags = [
    "崩坏3rd",
]

usernames = [
    "赤倉＠パーカー再販中"
]

illustrations = [
    86162743,
]

datasets_path = os.path.curdir + "/datasets"
normal_path = datasets_path + "/normal"
translated_path = datasets_path + "/translated"

bad_datasets_path = os.path.curdir + "/bad_datasets"
bad_normal_path = bad_datasets_path + "/normal"
bad_translated_path = bad_datasets_path + "/translated"

user_datasets_path = os.path.curdir + "/user_datasets"
user_normal_path = user_datasets_path + "/normal"
user_translated_path = user_datasets_path + "/translated"

related_datasets_path = os.path.curdir + "/related_datasets"
related_normal_path = related_datasets_path + "/normal"
related_translated_path = related_datasets_path + "/translated"

illegal_chars = ['/', '\\']

min_file = 5

max_tags = 100

max_users = 100

max_illusts = 10000

total_view = 1000
total_bookmarks = 50

downloaded_tag = {}
downloaded_user = {}
downloaded_related = {}
all_tags = set()

api = AppPixivAPI()
api.login(username="dreamers.dpf@gmail.com", password="19981104Dpf")


def make_tag_dir(dir_name, path=normal_path):
    path = os.path.join(path, dir_name)
    if os.path.exists(path):
        return False
    os.mkdir(path)
    return dir_name


# 评分高的图片
def highQualityCallback(value):
    return value.total_view >= total_view and value.total_bookmarks >= total_bookmarks and value.type == "illust"


# 评分低的图片
def lowQualityCallback(value):
    return value.total_view < total_view and value.total_bookmarks < total_bookmarks and value.type == "illust"


# 获取高质量图片，指评分高
def fetchHighQualityIllusts(word: str, limit=50) -> list:
    return fetchIllustsByQuality(word, limit, callback=highQualityCallback)


def fetchLowQualityIllusts(word: str, limit=50) -> list:
    return fetchIllustsByQuality(word, limit, callback=lowQualityCallback)


def fetchIllustsByQuality(word: str, limit=50, search=api.search_illust, callback=highQualityCallback) -> list:
    result = search(word)  # 按关键词搜索，比如崩崩崩
    image_results, i = list(filter(callback, result.illusts)), 0
    # 进度条
    bar = tqdm(ascii=True, desc="fetch images", colour="green", unit="per")
    bar.update(len(image_results))

    # 如果有下一页
    while result.next_url is not None and i < limit:
        next_qs = api.parse_qs(result.next_url)
        result = search(**next_qs)  # 搜索下一页的图片
        f = filter(callback, result.illusts if result.illusts is not None else [])
        image_results += list(f) if f is not None else []
        i += 1
        bar.update(len(image_results))

    bar.close()
    return image_results


def fetchIllustsByRelated(illust_id: int, limit=50) -> list:
    result = api.illust_related(illust_id)
    image_results, i = list(filter(highQualityCallback, result.illusts)), 0
    bar = tqdm(ascii=True, desc="fetch images from user", colour="yellow", unit="per")
    bar.update(len(image_results))
    while result.next_url is not None and i < limit:
        next_qs = api.parse_qs(result.next_url)
        result = api.illust_related(**next_qs)
        f = filter(highQualityCallback, result.illusts if result.illusts is not None else [])
        image_results += list(f) if f is not None else []
        bar.update(len(image_results))
        i += 1

    return image_results


def bfsIllustsByRelated(illust_id: int, limit=50) -> None:
    downloaded_related[illust_id] = True

    q = Queue()
    q.put(illust_id)
    while not q.empty():
        cur_illust_id = q.get()
        illusts = fetchIllustsByRelated(cur_illust_id)
        downloadIllusts(illusts, quality="medium", normal_path=related_normal_path,
                        translated_path=related_translated_path)
        if len(downloaded_related) > max_illusts:
            break

        for illust in illusts:
            id = illust.id
            if not downloaded_related.get(id):
                downloaded_related[id] = True
                q.put(id)


# 一个画师的所有插画
def fetchIllustsByUser(user_id: int, limit=100) -> list:
    results = api.user_illusts(user_id)
    image_results, i = list(filter(highQualityCallback, results.illusts)), 0
    bar = tqdm(ascii=True, desc="fetch images from user", colour="yellow", unit="per")
    bar.update(len(image_results))
    # 下一页
    while results.next_usr is not None and i < limit:
        next_qs = api.parse_qs(results)
        results = api.user_illusts(**next_qs)
        f = filter(highQualityCallback, results.illusts if results.illusts is not None else [])
        image_results += list(f) if f is not None else []
        i += 1
        bar.update(len(image_results))

    return image_results


# 获取所有图片
def fetchAllIllustrations(word: str, limit=100, search=api.search_illust) -> list:
    result = search(word)
    image_results, i = result.illusts, 0
    while result.next_url is not None and i < limit:
        next_qs = api.parse_qs(result.next_url)
        result = search(**next_qs)

        image_results += result.illusts
        i += 1

    return image_results


#  标签里面可能有 ABC/dd名称，需要将"/"转化掉
def check_name(pathname: str) -> bool:
    for ic in illegal_chars:
        if pathname.find(ic) != -1:
            return True

    return False


def rename(pathname: str) -> str:
    if check_name(pathname):
        for ic in illegal_chars:
            pathname = pathname.replace(ic, "_")
    return pathname


def is_less(result: list) -> bool:
    if len(result) < 10:
        return True
    return False


# 广搜下载图片
def breadthFirstSearch(word: str, quality="medium", n_path=normal_path,
                       t_path=translated_path, fetcher=fetchHighQualityIllusts) -> None:
    downloaded_tag[word] = True
    q = Queue()
    q.put(word)
    while not q.empty():
        cur_tag = q.get()
        image_results = fetcher(cur_tag)

        # 下载一堆图片，并返回图片里的标签
        tags = downloadIllusts(image_results, quality=quality, normal_path=n_path, translated_path=t_path)

        # 最多提取标签数量
        if len(downloaded_tag) > max_tags:
            break

        for t in tags:
            if not downloaded_tag.get(t):
                downloaded_tag[t] = True
                q.put(t)


def bfsIllustsOfUser(username: str) -> None:
    result = api.search_user(username)
    if len(result.user_previews) == 0:
        return
    user = result.user_previews[0]
    user_id = user.user.id
    downloaded_user[user_id] = True
    q = Queue()
    q.put(user_id)

    while not q.empty():
        cur_user_id = q.get()
        illusts = fetchIllustsByUser(cur_user_id)
        # print("illusts := ", illusts)
        downloadIllusts(illusts, quality="medium", normal_path=user_normal_path,
                        translated_path=user_translated_path)

        if len(downloaded_user) >= max_users:
            break

        following_users = api.user_following(cur_user_id).user_previews
        for user in following_users:
            user_id = user.user.id
            if downloaded_user.get(user_id) is None:
                downloaded_user[user_id] = True
                q.put(user_id)


# 移除图片少的标签
def remove_less_dir(pathname: str) -> None:
    ls_dir = [d for d in os.listdir(pathname) if os.path.isdir(os.path.join(pathname, d))]
    for d in ls_dir:
        path = os.path.join(pathname, d)
        size = len(os.listdir(path))
        if size < min_file:
            rmtree(path)


# 下载图片
def downloadIllusts(image_results: list, quality, normal_path, translated_path) -> set:
    if is_less(image_results):
        return set()
    all_image_tags = set()
    for image in tqdm(image_results, desc="download images", colour="white"):
        image_tags = image.tags
        url = image.image_urls[quality]
        image_id = image.id
        basename = str(image_id) + ".jpg"
        normal_tags = [rename(t.name) for t in image_tags]
        translate_tags = [rename(t.translated_name) for t in image_tags if t.translated_name is not None]

        for t in normal_tags:
            all_image_tags.add(t)
            make_tag_dir(t, path=normal_path)
        for t in translate_tags:
            make_tag_dir(t, path=translated_path)
        if len(normal_tags) == 0:
            normal_tags.append("__unknown__")
        image_normal_path = os.path.join(normal_path, normal_tags[0] + "/")
        # image_translate_path = os.path.join(translate_path, translate_tags[0] + "/")
        api.download(url, prefix=image_normal_path, name=basename)

        origin_path = os.path.join(image_normal_path, basename)

        for tag_index in range(1, len(normal_tags)):
            target_path = os.path.join(normal_path, normal_tags[tag_index], basename)
            if not os.path.exists(target_path):
                copyfile(origin_path, target_path)

        for tag_index in range(len(translate_tags)):
            target_path = os.path.join(translated_path, translate_tags[tag_index], basename)
            if not os.path.exists(target_path):
                copyfile(origin_path, target_path)
    return all_image_tags


def runScriptOfIllusts():
    if not os.path.exists(datasets_path):
        os.mkdir(datasets_path)
    if not os.path.exists(normal_path):
        os.mkdir(normal_path)
    if not os.path.exists(translated_path):
        os.mkdir(translated_path)

    for t in need_get_tags:
        breadthFirstSearch(t)

    # 删除图片少的标签
    remove_less_dir(normal_path)
    remove_less_dir(translated_path)


def runScriptOfBadIllusts():
    # 获取垃圾图片
    if not os.path.exists(bad_datasets_path):
        os.mkdir(bad_datasets_path)
    if not os.path.exists(bad_normal_path):
        os.mkdir(bad_normal_path)
    if not os.path.exists(bad_translated_path):
        os.mkdir(bad_translated_path)

    breadthFirstSearch(need_get_tags[0])

    remove_less_dir(bad_normal_path)
    remove_less_dir(bad_translated_path)


def runScriptOfUser():
    if not os.path.exists(user_datasets_path):
        os.mkdir(user_datasets_path)
    if not os.path.exists(user_normal_path):
        os.mkdir(user_normal_path)
    if not os.path.exists(user_translated_path):
        os.mkdir(user_translated_path)

    for username in usernames:
        bfsIllustsOfUser(username)

    remove_less_dir(user_normal_path)
    remove_less_dir(user_translated_path)


def runScriptOfRelated():
    if not os.path.exists(related_datasets_path):
        os.mkdir(related_datasets_path)
    if not os.path.exists(related_normal_path):
        os.mkdir(related_normal_path)
    if not os.path.exists(related_translated_path):
        os.mkdir(related_translated_path)

    for illust in illustrations:
        bfsIllustsByRelated(illust)

    remove_less_dir(related_normal_path)
    remove_less_dir(related_translated_path)


if __name__ == "__main__":
    # runScriptOfIllusts()
    # runScriptOfUser()
    runScriptOfRelated()
