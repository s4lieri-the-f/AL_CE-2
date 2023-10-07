import random

import vksender
import ad_generator
from datetime import datetime, timedelta
from time import sleep
from rich import print

log_id = 2000000014

# init
#alice = vksender.SimpleVKClient(token='vk1.a.wEYAF0npApY_UajdZIW_4excc3H_u82dpb24uPcAdJMEeUsDdATqu7Xnph91tI74igxCPAxXol2B61oP0t9AvhNRU_84pmdH-q6m38h1jpKNszKoZtpN0Ijob42ilOWcT5oSmQ0h8CLEnnDzODOKONc6QfSBMa4zAFLAamnS7BaMO_qZa5xKJdxSk8GAtgtv')

# теперь инициализировать всех платников муахаха
#alice.send_message(f"[{datetime.now()}] Main loopcycle initiated, now fetching data from DB, then waiting for midnight.", log_id)
ad = ad_generator.Ad("user_ad_groups.db3")
lifecycle_users = {}
users = ad.get_all_users()
for user in users:
    lifecycle_users[user[0]] = {'group': ad.get_user_group_id(user[0]),
                                'ad_groups': {key: [value[0][4]-12, value[0][4]] for key, value in [(x, ad.get_ad_group(x)) for x in ad.get_ad_groups(ad.get_user_group_id(user[0]))]}}
print(lifecycle_users)

#alice.send_message(f"[{datetime.now()}] Initiated {len(lifecycle_users)} users.", log_id)

# уебищное говно, но лучше стандартизировать
# Дожидаемся полуночи и начинаем ХУЯРИТЬ
ct = datetime.now()
midnight = ct.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
time_left = midnight - ct

#sleep(time_left.total_seconds())

while True:
    users = ad.get_all_users()
    if len(users) != len(lifecycle_users.keys()):
        to_delete = [x for x in lifecycle_users.keys() if x not in users]
        to_add = [x for x in users if x not in lifecycle_users.keys()]
        for x in to_delete:
            lifecycle_users.pop(x)
        for x in to_add:
            lifecycle_users[x] = {'group': ad.get_user_group_id(x[0]),
                                        'ad_groups': {key: [value[0][4] - 12, value[0][4]] for key, value in
                                                      [(x, ad.get_ad_group(x)) for x in
                                                       ad.get_ad_groups(ad.get_user_group_id(x[0]))]}}

    for group in lifecycle_users.keys():

        gr = lifecycle_users[group]
        if len(gr["ad_groups"].keys()) != ad.get_ad_groups(gr["group"]):
            to_delete = [x for x in gr["ad_groups"].keys() if x not in ad.get_ad_groups(gr["group"])]
            to_add = [x for x in ad.get_ad_groups(gr["group"]) if x not in gr["ad_groups"].keys()]
            for x in to_delete:
                gr["ad_groups"].pop(x)
            for x in to_add:
                gr["ad_groups"][x] = [ad.get_ad_group(x)[0][4] - 12, ad.get_ad_group(x)[0][4]]

        for ad_gr in gr["ad_groups"].keys():
            ad_group = gr["ad_groups"][ad_gr]
            ad_group[0] += 12
            if ad_group[0] == ad_group[1]:
                link, period, post, image = ad.assemble(gr['group'], ad_gr, random.choice(ad.get_ad_post_ids(gr['group'])))
                print(link)

    print(lifecycle_users)
    ct = datetime.now()
    midnight = ct.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=12)
    sleep((midnight - ct).total_seconds())


