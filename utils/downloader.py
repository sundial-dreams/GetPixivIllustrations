import os
from shutil import copyfile
from tqdm import tqdm
import time
from pixivpy3 import *
from .utils import is_less, rename, make_tag_dir, exception


def downloadIllusts(api: AppPixivAPI, image_results: list, quality, pathname) -> set:
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

        if len(normal_tags) == 0:
            continue

        for t in normal_tags:
            all_image_tags.add(t)
            make_tag_dir(t, path=n_path)

        for t in translate_tags:
            make_tag_dir(t, path=t_path)

        image_normal_path = os.path.join(n_path, normal_tags[0] + "/")
        # image_translate_path = os.path.join(translate_path, translate_tags[0] + "/")
        # 这张图片已经下载过
        origin_path = os.path.join(image_normal_path, basename)
        if os.path.exists(origin_path):
            continue

        _, e = exception(api.download)(url, prefix=image_normal_path, name=basename)

        if e is not None:
            time.sleep(10)
            continue

        # try:
        #     api.download(url, prefix=image_normal_path, name=basename)
        # except PixivError as e:
        #     time.sleep(10)
        #     continue

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
