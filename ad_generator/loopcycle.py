import random

import vksender
import ad_generator
from datetime import datetime, timedelta
from time import sleep
from rich import print

log_id = 2000000014

# init
alice = vksender.SimpleVKClient(token='vk1.a.wEYAF0npApY_UajdZIW_4excc3H_u82dpb24uPcAdJMEeUsDdATqu7Xnph91tI74igxCPAxXol2B61oP0t9AvhNRU_84pmdH-q6m38h1jpKNszKoZtpN0Ijob42ilOWcT5oSmQ0h8CLEnnDzODOKONc6QfSBMa4zAFLAamnS7BaMO_qZa5xKJdxSk8GAtgtv')

# теперь инициализировать всех платников муахаха
alice.send_message(f"[{datetime.now()}] Main loopcycle initiated, now fetching data from DB, then waiting for midnight.", log_id)
ad = ad_generator.Ad("user_ad_groups.db3")
lifecycle_users = {}
users = ad.get_all_users()
for user in users:
    lifecycle_users[user[0]] = {'group': ad.get_user_group_id(user[0]),
                                'ad_groups': {key: [value[0][4]-12, value[0][4]] for key, value in [(x, ad.get_ad_group(x)) for x in ad.get_ad_groups(ad.get_user_group_id(user[0]))]},
                                'log_chat_id': user[5],
                                'token': user[6],
                                'album_id': user[7]}
print(lifecycle_users)

alice.send_message(f"[{datetime.now()}] Initiated {len(lifecycle_users)} users.", log_id)

# уебищное говно, но лучше стандартизировать
# Дожидаемся полуночи и начинаем ХУЯРИТЬ
ct = datetime.now()
midnight = ct.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
time_left = midnight - ct
print(time_left)

sleep(time_left.total_seconds())

while True:
    users = ad.get_all_users()
    if len(users) != len(lifecycle_users.keys()):
        to_delete = [x for x in lifecycle_users.keys() if x not in users]
        to_add = [x for x in users if x not in lifecycle_users.keys()]
        for x in to_delete:
            lifecycle_users.pop(x)
        for x in to_add:
            lifecycle_users[x] = {  'group': ad.get_user_group_id(x[0]),
                                    'ad_groups': {key: [value[0][4] - 12, value[0][4]] for key, value in
                                                      [(x, ad.get_ad_group(x)) for x in
                                                       ad.get_ad_groups(ad.get_user_group_id(x[0]))]},
                                    'log_chat_id': x[5],
                                    'token': x[6],
                                    'album_id': x[7]}

    for group in lifecycle_users.keys():
        gr = lifecycle_users[group]
        if gr["token"]:
            logger = vksender.SimpleVKClient(token=gr["token"])
            if gr["album_id"] == None:
                logger.create_album('AL_CE-2 cog')
        if len(gr["ad_groups"].keys()) != ad.get_ad_groups(gr["group"]):
            to_delete = [x for x in gr["ad_groups"].keys() if x not in ad.get_ad_groups(gr["group"])]
            to_add = [x for x in ad.get_ad_groups(gr["group"]) if x not in gr["ad_groups"].keys()]
            for x in to_delete:
                gr["ad_groups"].pop(x)
            for x in to_add:
                gr["ad_groups"][x] = [ad.get_ad_group(x)[0][4] - 12, ad.get_ad_group(x)[0][4]]

        if not gr["token"]:
            continue
        logger.send_message(f"[{datetime.now()}] Started ad sending process.", gr["log_chat_id"])
        for ad_gr in gr["ad_groups"].keys():
            ad_group = gr["ad_groups"][ad_gr]
            ad_group[0] += 12
            if ad_group[0] == ad_group[1]:
                link, period, post, image = ad.assemble(gr['group'], ad_gr, random.choice(ad.get_ad_post_ids(gr['group'])))
                logger.send_message(f"[{datetime.now()}] Sending an ad to {link}, next in {period}", gr["log_chat_id"])
                for img in image:
                    if not ad.get_image_by_id(img[0])[0][3]:
                        ad.update_image(img[0], logger.save_image(ad.get_image_by_id(img[0])[0][2], gr["album_id"]))
                result = logger.wall_post(id=ad_gr, text=post, image_id=",".join([ad.get_image_by_id(x[0])[0][3] for x in img]))
                # print(result)
    print(lifecycle_users)
    sleep(timedelta(hours=12).total_seconds())


