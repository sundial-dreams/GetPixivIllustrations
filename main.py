from pixivpy3 import *
import os
from shutil import copyfile, rmtree
from tqdm import trange, tqdm
from queue import Queue
import time

need_get_tags = [
    "崩坏3rd",
]

usernames = [
    # "ふーみ",
    # "Hiten",
    "MISSILE228",
    "やすの",
    "赤倉＠パーカー再販中",
    "torino",
    "ののこ",
    "ひろ@リクエスト募集中",
    "宮瀬まひろ",
    "Rosuuri",
    "ふわり",
    "きさらぎゆり",
    "Roha",
    "mocha＠３日目南-ナ31a",
    "コーラ",
    "ふゆの",
    "Rafa",
    "ke-ta"
]

illustrations = [
    # 84479370,
    # 83198266,
    # 86102247,
    # 72471572,
    # 84831308,
    # 86122864,
    # 59665299,
    # 80134146,
    # 57526556,
    # 75630726,
    # 76138376,
    # 73136818,
    # 60806246,
    # 36385948,
    # 64481817,
    # 44920385,
    77944010
]

datasets_path = os.path.curdir + "/datasets"
normal_path = datasets_path + "/normal"
translated_path = datasets_path + "/translated"

bad_datasets_path = os.path.curdir + "/bad_datasets"
bad_normal_path = bad_datasets_path + "/normal"
bad_translated_path = bad_datasets_path + "/translated"

# 插画存放路径
user_datasets_path = os.path.curdir + "/user_datasets"

related_datasets_path = os.path.curdir + "/related_datasets"

# 标签中不合法字符
ILLEGAL_CHARS = ['/', '\\', '-', '!', '~', ',', ':']
# 最小文件数量
MIN_FILES = 10
# 搜索最大标签深度
MAX_TAGS = 400
# 搜索最大用户深度
MAX_USERS = 5
# 搜索最大相关深度
MAX_ILLUSTS = 10
# 插画观看的最小人数
TOTAL_VIEW = 1000
# 插画点赞的最小人数
TOTAL_BOOKMARKS = 50
# 下载图片的质量, large | medium
ILLUSTS_QUALITY = "medium"

# 已下载
downloaded_tag = {}
downloaded_user = {}
downloaded_related = {}
# 标签集合
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
    return value.TOTAL_VIEW >= TOTAL_VIEW and value.TOTAL_BOOKMARKS >= TOTAL_BOOKMARKS and value.type == "illust"


# 评分低的图片
def lowQualityCallback(value):
    return value.TOTAL_VIEW < TOTAL_VIEW and value.TOTAL_BOOKMARKS < TOTAL_BOOKMARKS and value.type == "illust"


# 获取高质量图片，指评分高
def fetchHighQualityIllusts(word: str, limit=50) -> list:
    return fetchIllustsByQuality(word, limit, callback=highQualityCallback)


def fetchLowQualityIllusts(word: str, limit=50) -> list:
    return fetchIllustsByQuality(word, limit, callback=lowQualityCallback)


def fetchIllustsByQuality(word: str, limit=50, search=api.search_illust, callback=highQualityCallback) -> list:
    result = search(word)  # 按关键词搜索，比如崩崩崩
    image_results, i = list(filter(callback, result.illusts if result.illusts is not None else [])), 0
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
        bar.update(len(list(f)))

    bar.close()
    return image_results


# 获取对应插画相关的作品
def fetchIllustsByRelated(illust_id: int, limit=10) -> list:
    try:
        results = api.illust_related(illust_id)
    except PixivError as e:
        time.sleep(10)
        return []
    # 兜底
    if results is None:
        return []

    illusts = results.get("illusts", [])
    if len(illusts) == 0:
        return []

    image_results, i = list(filter(highQualityCallback, illusts)), 0

    if len(image_results) == 0:
        return []

    # 进度条
    bar = tqdm(ascii=True, desc="fetch images from related", colour="yellow", unit="per")
    bar.update(len(image_results))
    while results.next_url is not None and i < limit:
        next_qs = api.parse_qs(results.next_url)
        try:
            results = api.illust_related(**next_qs)
        except PixivError as e:
            time.sleep(10)
            return image_results
        illusts = results.get("illusts", [])
        f = filter(highQualityCallback, illusts)
        image_results += list(f)
        bar.update(len(list(f)))
        i += 1

    return image_results


# 广度优先搜索相关的插画作品
def bfsIllustsByRelated(illust_id: int) -> None:
    downloaded_related[illust_id] = True

    q = Queue()
    q.put(illust_id)
    count = 0
    while not q.empty():
        cur_illust_id = q.get()
        illusts = fetchIllustsByRelated(cur_illust_id)

        time.sleep(10)  # 歇息10s
        downloadIllusts(illusts, quality=ILLUSTS_QUALITY, pathname=related_datasets_path)
        # 循环退出条件
        if count > MAX_ILLUSTS:
            break

        for illust in illusts:
            illust_id = illust.get("id", 0)
            if not downloaded_related.get(illust_id):
                downloaded_related[illust_id] = True
                q.put(illust_id)
        count += 1


# 一个画师的所有插画
def fetchIllustsByUser(user_id: int, limit=100) -> list:
    try:
        results = api.user_illusts(user_id)
    except PixivError as e:
        time.sleep(10)
        return []

    if results is None:
        return []

    illusts = results.get("illusts", [])
    if len(illusts) == 0:
        return []

    image_results, i = list(filter(highQualityCallback, illusts)), 0
    # 进度条
    bar = tqdm(ascii=True, desc="fetch images from user", colour="yellow", unit="per")
    bar.update(len(image_results))
    # 下一页
    while results.next_url is not None and i < limit:
        next_qs = api.parse_qs(results.next_url)
        try:
            results = api.user_illusts(**next_qs)
        except PixivError as e:
            time.sleep(10)
            return image_results

        illusts = results.get("illusts", [])
        f = filter(highQualityCallback, illusts)
        image_results += list(f)
        i += 1
        bar.update(len(list(f)))

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


# 广搜下载图片
def bfsIllustsOfTags(word: str, fetcher=fetchHighQualityIllusts) -> None:
    downloaded_tag[word] = True
    q = Queue()
    q.put(word)
    while not q.empty():
        cur_tag = q.get()
        image_results = fetcher(cur_tag)

        # 下载一堆图片，并返回图片里的标签
        tags = downloadIllusts(image_results, quality=ILLUSTS_QUALITY, pathname=datasets_path)

        # 最多提取标签数量
        if len(downloaded_tag) > MAX_TAGS:
            break

        for t in tags:
            if not downloaded_tag.get(t):
                downloaded_tag[t] = True
                q.put(t)


# 从一位画师开始搜索，再搜索这位画师关注的画师的作品
def bfsIllustsOfUser(username: str) -> None:
    try:
        results = api.search_user(username)
    except PixivError as e:
        return

    if results is None:
        return

    users = results.get("user_previews", [])
    if len(users) == 0:
        return

    user = users[0]
    user_id = user.get("user", {}).get("id", 0)
    # user_id = user.user.id  # 拿到画师的ID
    # 这位画师已经搜过啦
    if downloaded_user.get(user_id):
        return

    downloaded_user[user_id] = True
    q = Queue()
    q.put(user_id)
    count = 0

    while not q.empty():
        cur_user_id = q.get()
        illusts = fetchIllustsByUser(cur_user_id)
        time.sleep(20)  # 歇息20s再下载

        # 下载图片 quality="large"时为下载原图
        downloadIllusts(illusts, quality=ILLUSTS_QUALITY, pathname=user_datasets_path)
        # 循环退出条件
        if count >= MAX_USERS:
            break
        # 获取这位画师所关注的画师
        try:
            following_users = api.user_following(cur_user_id).get("user_previews", [])
        except PixivError as e:
            time.sleep(10)
            continue

        for user in following_users:
            user_id = user.get("user", {}).get("id", 0)
            # user_id = user.user.id
            if downloaded_user.get(user_id) is None:
                downloaded_user[user_id] = True
                q.put(user_id)
        count += 1


# 移除图片少的标签
def rm_less_tags(pathname: str) -> None:
    ls_dir = [d for d in os.listdir(pathname) if os.path.isdir(os.path.join(pathname, d))]
    for d in ls_dir:
        path = os.path.join(pathname, d)
        size = len(os.listdir(path))
        if size < MIN_FILES:
            rmtree(path)


# 下载图片
def downloadIllusts(image_results: list, quality, pathname) -> set:
    if is_less(image_results):
        return set()
    all_image_tags = set()
    max_num = 100
    count = 0
    n_path = pathname + "/normal"
    t_path = pathname + "/translated"
    for image in tqdm(image_results, desc="download images", colour="white"):
        image_tags = image.get("tags", [])
        url = image.get("image_urls", {}).get(quality, None)
        # url = image.image_urls[quality] if image.image_urls is not None else None
        image_id = image.get("id", None)

        if url is None or image_id is None:
            continue

        basename = str(image_id) + ".jpg"
        normal_tags = [rename(t.name) for t in image_tags]
        translate_tags = [rename(t.translated_name) for t in image_tags if t.translated_name is not None]

        for t in normal_tags:
            all_image_tags.add(t)
            make_tag_dir(t, path=n_path)
        for t in translate_tags:
            make_tag_dir(t, path=t_path)
        if len(normal_tags) == 0:
            normal_tags.append("__unknown__")
        image_normal_path = os.path.join(n_path, normal_tags[0] + "/")
        # image_translate_path = os.path.join(translate_path, translate_tags[0] + "/")
        # 这张图片已经下载过
        origin_path = os.path.join(image_normal_path, basename)
        if os.path.exists(origin_path):
            continue

        try:
            api.download(url, prefix=image_normal_path, name=basename)
        except PixivError as e:
            time.sleep(10)
            continue

        for tag_index in range(1, len(normal_tags)):
            target_path = os.path.join(n_path, normal_tags[tag_index], basename)
            if not os.path.exists(target_path):
                copyfile(origin_path, target_path)

        for tag_index in range(len(translate_tags)):
            target_path = os.path.join(t_path, translate_tags[tag_index], basename)
            if not os.path.exists(target_path):
                copyfile(origin_path, target_path)
        count += 1

        if count > max_num:
            time.sleep(10)  # 歇息10s
            count = 0

    return all_image_tags


def runScriptOfIllusts():
    if not os.path.exists(datasets_path):
        os.mkdir(datasets_path)
    if not os.path.exists(normal_path):
        os.mkdir(normal_path)
    if not os.path.exists(translated_path):
        os.mkdir(translated_path)

    for t in need_get_tags:
        bfsIllustsOfTags(t)

    # 删除图片少的标签
    rm_less_tags(normal_path)
    rm_less_tags(translated_path)


def runScriptOfBadIllusts():
    # 获取垃圾图片
    if not os.path.exists(bad_datasets_path):
        os.mkdir(bad_datasets_path)
    if not os.path.exists(bad_normal_path):
        os.mkdir(bad_normal_path)
    if not os.path.exists(bad_translated_path):
        os.mkdir(bad_translated_path)

    bfsIllustsOfTags(need_get_tags[0])

    rm_less_tags(bad_normal_path)
    rm_less_tags(bad_translated_path)


def runScriptOfUser():
    user_normal_path = user_datasets_path + "/normal"
    user_translated_path = user_datasets_path + "/translated"
    if not os.path.exists(user_datasets_path):
        os.mkdir(user_datasets_path)
    if not os.path.exists(user_normal_path):
        os.mkdir(user_normal_path)
    if not os.path.exists(user_translated_path):
        os.mkdir(user_translated_path)

    cur_name = ""
    try:
        for username in usernames:
            cur_name = username
            bfsIllustsOfUser(username)
            # time.sleep(60)  # 歇息1分钟再去下载另一位画师

    except OSError as e:
        print("next_username := ", cur_name)

    rm_less_tags(user_normal_path)
    rm_less_tags(user_translated_path)


def runScriptOfRelated():
    related_normal_path = related_datasets_path + "/normal"
    related_translated_path = related_datasets_path + "/translated"

    if not os.path.exists(related_datasets_path):
        os.mkdir(related_datasets_path)
    if not os.path.exists(related_normal_path):
        os.mkdir(related_normal_path)
    if not os.path.exists(related_translated_path):
        os.mkdir(related_translated_path)
    cur_id = 0
    try:
        for illust in illustrations:
            cur_id = illust
            bfsIllustsByRelated(illust)
    except OSError as e:
        print("next_id := ", cur_id)

    rm_less_tags(related_normal_path)
    rm_less_tags(related_translated_path)


if __name__ == "__main__":
    # runScriptOfRelated()
    # time.sleep(60)
    runScriptOfUser()
