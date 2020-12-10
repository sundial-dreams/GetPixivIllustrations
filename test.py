from pixivpy3 import *

if __name__ == "__main__":
    api = AppPixivAPI()
    api.login(username="dreamers.dpf@gmail.com", password="19981104Dpf")
    # api.login(username="2031163243@qq.com", password="19981104Dpf")
    # r = api.search_illust("崩坏三")
    # print(r)
    #
    # image = r.illusts[0]
    # api.download("https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/12/09/00/57/06/86183261_p0_master1200.jpg")
    r = api.search_user("赤倉＠パーカー再販中")
    print(r)
    user_id = r.user_previews[0].user.id
    print(user_id)

    r = api.user_following(user_id)
    print(r)

    r = api.user_follower(user_id)
    print(r)

    # api.user_illusts()