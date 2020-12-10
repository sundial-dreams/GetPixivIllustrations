from pixivpy_async import *
from os import path, mkdir, listdir
from shutil import copyfile, rmtree
from queue import Queue
import asyncio

datasets_path = path.curdir + "/async_datasets"
normal_path = datasets_path + "/normal"
translated_path = datasets_path + "/translated"

tags = [

]

illegal_chars = ['/', '\\']
min_file_num = 5

max_tags = 1000
total_view = 1000
total_bookmarks = 40
downloaded_tags = {}
all_tags = set()


def make_tag_dir(dir_name, pathname=normal_path):
    pathname = path.join(pathname, dir_name)
    if path.exists(pathname):
        return False
    mkdir(pathname)
    return dir_name


# 评分高的图片
def highQualityCallback(value):
    return value.total_view >= total_view and value.total_bookmarks >= total_bookmarks and value.type == "illust"


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
    if len(result) < 36:
        return True
    return False


async def fetchImagesByQuality(api: AppPixivAPI, word: str, limit=100, callback=highQualityCallback) -> list:
    result = await api.search_illust(word)
    image_results, i = list(filter(callback, result.illusts)), 0
    while result.next_url is not None and i < limit:
        next_qs = api.parse_qs(result.next_url)
        result = await api.search_illust(**next_qs)
        f = filter(callback, result.illusts if result.illusts is not None else [])
        image_results += list(f) if f is not None else []
        i += 1
    return image_results


async def fetchHighQualityImages(api: AppPixivAPI, word: str, limit=100) -> list:
    return await fetchImagesByQuality(api, word, limit, highQualityCallback)


async def downloadImages(api: AppPixivAPI, image_results: list, quality, normal_path, translated_path) -> set:
    if is_less(image_results):
        return set()
    all_image_tags = set()
    for image in image_results:
        image_tags = image.tags
        url = image.image_urls[quality]
        image_id = image.id
        basename = str(image_id) + ".jpg"
        normal_tags = [rename(t.name) for t in image_tags]
        translate_tags = [rename(t.translated_name) for t in image_tags if t.translated_name is not None]

        for t in normal_tags:
            all_image_tags.add(t)
            make_tag_dir(t)
        for t in translate_tags:
            make_tag_dir(t, pathname=translated_path)
        if len(normal_tags) == 0:
            normal_tags.append("__unknown__")
        image_normal_path = path.join(normal_path, normal_tags[0] + "/")
        # image_translate_path = os.path.join(translate_path, translate_tags[0] + "/")
        await api.download(url, prefix=image_normal_path, name=basename)

        origin_path = path.join(image_normal_path, basename)

        for tag_index in range(1, len(normal_tags)):
            target_path = path.join(normal_path, normal_tags[tag_index], basename)
            if not path.exists(target_path):
                copyfile(origin_path, target_path)

        for tag_index in range(len(translate_tags)):
            target_path = path.join(translated_path, translate_tags[tag_index], basename)
            if not path.exists(target_path):
                copyfile(origin_path, target_path)
    return all_image_tags


# 广搜下载图片
async def breadthFirstSearch(api: AppPixivAPI, word: str, quality="medium", n_path=normal_path,
                             t_path=translated_path, fetcher=fetchHighQualityImages) -> None:
    downloaded_tags[word] = True
    q = Queue()
    q.put(word)
    while not q.empty():
        cur_tag = q.get()
        image_results = await fetcher(api, cur_tag)

        # 下载一堆图片，并返回图片里的标签
        other_tags = await downloadImages(api, image_results, quality=quality, normal_path=n_path,
                                          translated_path=t_path)

        # 最多提取标签数量
        if len(downloaded_tags) > max_tags:
            break

        for t in other_tags:
            if not downloaded_tags.get(t):
                downloaded_tags[t] = True
                q.put(t)


def create_datasets_dir() -> None:
    if not path.exists(datasets_path):
        mkdir(datasets_path)
    if not path.exists(normal_path):
        mkdir(normal_path)
    if not path.exists(translated_path):
        mkdir(translated_path)


# 移除图片少的标签
def remove_less_dir(pathname: str) -> None:
    ls_dir = [d for d in listdir(pathname) if path.isdir(path.join(pathname, d))]
    for d in ls_dir:
        pathname = path.join(pathname, d)
        size = len(listdir(pathname))
        if size < min_file_num:
            rmtree(pathname)

async def main_loop():
    async with PixivClient() as client:
        aapi = AppPixivAPI(client=client)
        await aapi.login(username="dreamers.dpf@gmail.com", password="19981104Dpf")

        await breadthFirstSearch(aapi, "崩坏三")

        remove_less_dir(normal_path)
        remove_less_dir(translated_path)

if __name__ == "__main__":
    create_datasets_dir()
    asyncio.run(main_loop())


