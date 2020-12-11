import time
from pixivpy3 import *
from queue import Queue
from .fetcher import fetchIllustsByUser, fetchHighQualityIllusts, fetchIllustsByRelated
from .downloader import downloadIllusts
from .constants import MAX_USERS, MAX_ILLUSTS, MAX_TAGS, ILLUSTS_QUALITY
from .utils import exception

# 已下载
downloaded_tag = {}
downloaded_user = {}
downloaded_related = {}

# 从一位画师开始搜索，再搜索这位画师关注的画师的作品
def bfsIllustsOfUser(api: AppPixivAPI, username: str, datasets_pathname: str) -> None:

    results, e = exception(api.search_user)(username)
    # try:
    #     results = api.search_user(username)
    # except PixivError as e:
    #     return

    if e is not None:
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
        illusts = fetchIllustsByUser(api, cur_user_id)
        time.sleep(20)  # 歇息20s再下载

        # 下载图片 quality="large"时为下载原图
        downloadIllusts(api, illusts, quality=ILLUSTS_QUALITY, pathname=datasets_pathname)
        # 循环退出条件
        if count >= MAX_USERS:
            break
        # 获取这位画师所关注的画师

        results, e = exception(api.user_following)(cur_user_id)
        if e is not None:
            time.sleep(10)
            continue

        following_users = results.get("user_previews", [])
        # try:
        #     following_users = api.user_following(cur_user_id).get("user_previews", [])
        # except PixivError as e:
        #     time.sleep(10)
        #     continue

        for user in following_users:
            user_id = user.get("user", {}).get("id", 0)
            # user_id = user.user.id
            if downloaded_user.get(user_id) is None:
                downloaded_user[user_id] = True
                q.put(user_id)
        count += 1

# 广度优先搜索相关的插画作品
def bfsIllustsByRelated(api: AppPixivAPI, illust_id: int, datasets_pathname: str) -> None:
    downloaded_related[illust_id] = True

    q = Queue()
    q.put(illust_id)
    count = 0
    while not q.empty():
        cur_illust_id = q.get()
        illusts = fetchIllustsByRelated(api, cur_illust_id)

        time.sleep(10)  # 歇息10s
        downloadIllusts(api, illusts, quality=ILLUSTS_QUALITY, pathname=datasets_pathname)
        # 循环退出条件
        if count > MAX_ILLUSTS:
            break

        for illust in illusts:
            illust_id = illust.get("id", 0)
            if not downloaded_related.get(illust_id):
                downloaded_related[illust_id] = True
                q.put(illust_id)
        count += 1


# 广搜下载图片
def bfsIllustsOfTags(api: AppPixivAPI, word: str, datasets_pathname: str) -> None:
    downloaded_tag[word] = True
    q = Queue()
    q.put(word)
    while not q.empty():
        cur_tag = q.get()
        image_results = fetchHighQualityIllusts(api, cur_tag)

        # 下载一堆图片，并返回图片里的标签
        tags = downloadIllusts(image_results, quality=ILLUSTS_QUALITY, pathname=datasets_pathname)

        # 最多提取标签数量
        if len(downloaded_tag) > MAX_TAGS:
            break

        for t in tags:
            if not downloaded_tag.get(t):
                downloaded_tag[t] = True
                q.put(t)
