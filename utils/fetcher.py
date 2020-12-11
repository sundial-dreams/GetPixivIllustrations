import time
from pixivpy3 import *
from tqdm import tqdm
from .utils import highQualityCallback, lowQualityCallback, exception


# 一个画师的所有插画
def fetchIllustsByUser(api: AppPixivAPI, user_id: int, limit=100) -> list:
    results, e = exception(api.user_illusts)(user_id)
    if e is not None:
        time.sleep(10)
        return []
    # try:
    #     results = api.user_illusts(user_id)
    # except PixivError as e:
    #     time.sleep(10)
    #     return []

    if results is None:
        return []

    illusts = results.get("illusts", [])

    if len(illusts) == 0:
        return []

    image_results, i = list(filter(highQualityCallback, illusts)), 0
    # 进度条
    bar = tqdm(ascii=True, desc="fetch images from user", unit="per")
    bar.update(len(image_results))
    # 下一页
    while results.next_url is not None and i < limit:
        next_qs = api.parse_qs(results.next_url)
        results, e = exception(api.user_illusts)(**next_qs)

        if e is not None:
            time.sleep(10)
            return image_results

        # try:
        #     results = api.user_illusts(**next_qs)
        # except PixivError as e:
        #     time.sleep(10)
        #     return image_results

        illusts = results.get("illusts", [])
        f = filter(highQualityCallback, illusts)
        image_results += list(f)
        i += 1
        bar.update(len(list(f)))

    return image_results


# 获取对应插画相关的作品
def fetchIllustsByRelated(api: AppPixivAPI, illust_id: int, limit=10) -> list:
    results, e = exception(api.illust_related)(illust_id)
    if e is not None:
        time.sleep(10)
        return []

    # try:
    #     results = api.illust_related(illust_id)
    # except PixivError as e:
    #     time.sleep(10)
    #     return []
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
    bar = tqdm(ascii=True, desc="fetch images from related", unit="per")
    bar.update(len(image_results))
    while results.next_url is not None and i < limit:
        next_qs = api.parse_qs(results.next_url)
        results, e = exception(api.illust_related)(**next_qs)

        if e is not None:
            time.sleep(10)
            return image_results

        # try:
        #     results = api.illust_related(**next_qs)
        # except PixivError as e:
        #     time.sleep(10)
        #     return image_results

        illusts = results.get("illusts", [])
        f = filter(highQualityCallback, illusts)
        image_results += list(f)
        bar.update(len(list(f)))
        i += 1

    return image_results


# 获取所有图片
def fetchAllIllusts(api: AppPixivAPI, word: str, limit=100) -> list:
    result = api.search_illust(word)
    image_results, i = result.illusts, 0
    while result.next_url is not None and i < limit:
        next_qs = api.parse_qs(result.next_url)
        result = api.search_illust(**next_qs)

        image_results += result.illusts
        i += 1

    return image_results


def fetchIllustsByQuality(api: AppPixivAPI, word: str, limit=50, callback=highQualityCallback) -> list:
    result = api.search_illust(word)  # 按关键词搜索，比如崩崩崩
    image_results, i = list(filter(callback, result.illusts if result.illusts is not None else [])), 0
    # 进度条
    bar = tqdm(ascii=True, desc="fetch images", colour="green", unit="per")
    bar.update(len(image_results))

    # 如果有下一页
    while result.next_url is not None and i < limit:
        next_qs = api.parse_qs(result.next_url)
        result = api.search_illust(**next_qs)  # 搜索下一页的图片
        f = filter(callback, result.illusts if result.illusts is not None else [])
        image_results += list(f) if f is not None else []
        i += 1
        bar.update(len(list(f)))

    bar.close()
    return image_results


# 获取高质量图片，指评分高
def fetchHighQualityIllusts(api: AppPixivAPI, word: str, limit=50) -> list:
    return fetchIllustsByQuality(api, word, limit, callback=highQualityCallback)


def fetchLowQualityIllusts(api: AppPixivAPI, word: str, limit=50) -> list:
    return fetchIllustsByQuality(api, word, limit, callback=lowQualityCallback)
