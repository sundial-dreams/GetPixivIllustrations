import os
import time
from pixivpy3 import *
from utils.bfser import bfsIllustsOfUser, bfsIllustsByRelated
from utils.utils import rm_less_tags, checkpoint, log

usernames = [
    "ふーみ",
    "Hiten",
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
    84479370,
    83198266,
    86102247,
    72471572,
    84831308,
    86122864,
    59665299,
    80134146,
    57526556,
    75630726,
    76138376,
    73136818,
    60806246,
    36385948,
    64481817,
    44920385,
    77944010,
    47621790,
    59190594,
    76596270,
    82432085,
    62854107,
    76916493,
    54652001,
    63629527,
    44873217,
    81187455,
]

USERNAME = "dreamers.dpf@gmail.com"
PASSWORD = "19981104Dpf"
# 插画存放路径
user_datasets_path = os.path.curdir + "/user_datasets"

related_datasets_path = os.path.curdir + "/related_datasets"

api = AppPixivAPI()
api.login(username=USERNAME, password=PASSWORD)


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
            checkpoint("downloaded user: %s" % username)
            bfsIllustsOfUser(api, username, user_datasets_path)

            # time.sleep(60)  # 歇息1分钟再去下载另一位画师

    except Exception as e:
        log(e)
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
            checkpoint("downloaded illust: %s" % illust)
            bfsIllustsByRelated(api, illust, related_datasets_path)

    except Exception as e:
        log(e)
        print("next_id := ", cur_id)

    rm_less_tags(related_normal_path)
    rm_less_tags(related_translated_path)


if __name__ == "__main__":
    runScriptOfRelated()
    time.sleep(60)
    runScriptOfUser()
