import pickle
import time
import json
import sqlite3
from datetime import datetime
from typing import Union, Any

from instagrapi import Client


class ClientInterface:

    def __init__(self):
        self.con = sqlite3.connect('data.db')
        self.cur = self.con.cursor()
        self.user_id, self.device, self.username, self.password = \
            self.cur.execute('select * from user_data').fetchone()
        self.client = Client()

    def login(self) -> bool:
        self.set_settings()
        return self.client.login(self.username, self.password)

    def set_settings(self) -> None:
        if self.device:
            device = json.loads(self.device)
            self.client.set_settings(device)

    def dump_settings(self) -> None:
        device_dump = json.dumps(self.client.get_settings())
        self.cur.execute('update user_data set device = ? where id = ?', (device_dump, self.user_id))
        self.con.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.dump_settings()

    def collect_followers(self, target_username: str, amount: int = 0) -> tuple:   # 20 sec amount = 6921
        print('collecting followers of %s' % target_username)
        target_user_id = self.client.user_id_from_username(target_username)
        followers_id = self.client.user_followers_v1_chunk(target_user_id, max_amount=amount)  # id
        return followers_id

    def follow(self, target_id: str):
        self.client.user_follow(target_id)

    def collect_followings(self, target_username: str):
        print('collecting followings of %s' % target_username)
        target_user_id = self.client.user_id_from_username(target_username)
        followings = self.client.user_following_v1(target_user_id)
        return followings


def to_pickle(followers_data: Any, file_name):
    with open(file_name, 'wb') as file:
        pickle.dump(followers_data, file)


def from_pickle(file_name: str):
    with open(file_name, 'rb') as file:
        data = pickle.load(file)
    return data


def main(client: ClientInterface):
    target = 'panda__volkova'
    followers = client.collect_followers(target, 1000)[0]
    followings = client.collect_followings('alexey.naidiuk')

    to_pickle(followers, f'{target}_followers.pickle')
    to_pickle(followings, 'my_followings.pickle')

    non_followed = set(i.pk for i in followers) - set(i.pk for i in followings)

    c = 0
    iterable_followers = iter(non_followed)
    while c < 600:
        follower = next(iterable_followers)
        target_info = client.client.user_info_v1(follower)
        if not target_info.is_private and target_info.media_count > 10 \
                and 4000 >= target_info.follower_count >= 400 and 1000 >= target_info.following_count >= 100:
            client.follow(target_info.pk)
            print(target_info)
            c += 1
            print('followed %s' % c)
            if c % 100 == 0:
                print('sleeping for 1 hour')
                time.sleep(60*15)


def develop(client: ClientInterface):
    pass


if __name__ == '__main__':
    with ClientInterface() as client:
        login = client.login()
        main(client)
