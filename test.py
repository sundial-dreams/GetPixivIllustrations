from pixivpy3 import *
from utils.utils import exception, log, checkpoint

if __name__ == "__main__":
    api = AppPixivAPI()
    # api.login(username="dreamers.dpf@gmail.com", password="19981104Dpf")
    # api.login(username="2031163243@qq.com", password="19981104Dpf")
    # r = api.search_illust("崩坏三")
    # print(r)
    #
    # image = r.illusts[0]
    # api.download("https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/12/09/00/57/06/86183261_p0_master1200.jpg")
    r, e = exception(api.search_user)("ふーみ")
    if e is not None:
        log(e)
    print(r)
    user_id = ""
    print(user_id)

    r, e = exception(api.user_following)(user_id)
    if e is not None:
        checkpoint("some")

    print(r)

    r, e = exception(api.user_follower)(user_id)
    if e is not None:
        log(e)
    print(r)

    # api.user_illusts()
