import argparse
import json
import logging
import pickle
import sqlite3
from datetime import datetime, timedelta
from multiprocessing.pool import ThreadPool
from pathlib import Path
from time import sleep
from typing import List

from instagrapi import Client
from instagrapi.types import UserShort


class ClientInterface:

    def __init__(self, username: str, password: str, device: dict = None):
        self.username, self.password, self.device = username, password, device
        self.client = Client()
        self.set_settings()

    def login(self) -> bool:
        return self.client.login(self.username, self.password)

    def set_settings(self) -> None:
        if Path('dumped_settings.json').exists():
            dumped_settings = json.load(open('dumped_settings.json'))
            self.client.set_settings(dumped_settings)
        else:
            self.client.set_settings(
                {
                    'user_agent': 'Instagram 217.0.0.15.474 Android (30/11; 450dpi; 10'
                                  '80x2179; samsung; SM-A725F; a72q; qcom; en_US; 343997935)',
                    "device_settings": {
                        "app_version": "217.0.0.15.474",
                        "android_version": "30/11",
                        "android_release": "11",
                        "dpi": "450dpi",
                        "resolution": "1080x2179",
                        "manufacturer": "samsung",
                        "device": "a72q",
                        "model": "SM-A725F",
                        "cpu": "qcom",
                        "version_code": "343997935"
                    }
                }
            )

    def dump_settings(self) -> None:
        self.client.dump_settings(
            Path('dumped_settings.json')
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.dump_settings()

    def collect_followers(self, target_username: str, amount: int = 0) -> tuple[list[UserShort], str]:
        return_value = ()
        print('collecting followers of %s\n' % target_username)
        target_user_id = self.client.user_id_from_username(target_username)
        while not return_value:
            try:
                return_value = self.client.user_followers_v1_chunk(target_user_id, max_amount=amount)  # id
            except Exception as error:
                logging.error(error)
        return return_value

    def collect_followings(self, target_username: str, max_amount: int = 0) -> List[UserShort]:
        return_value = []
        print('collecting followings of %s\n' % target_username)
        target_user_id = self.client.user_id_from_username(target_username)
        try:
            return_value = self.client.user_following_v1(target_user_id, amount=max_amount)
        except Exception as error:
            logging.error(error)
        finally:
            return return_value

    def follow(self, target_id: str):
        self.client.user_follow(target_id)


def to_pickle(data, file_name):
    with open(file_name, 'wb') as file:
        pickle.dump(data, file)


def from_pickle(file_name: str):
    with open(file_name, 'rb') as file:
        data = pickle.load(file)
    return data


class Follow:

    def __init__(self, client: ClientInterface, targets_list: list, from_backup: bool = False):
        self.client = client
        self.targets = targets_list
        self.followed_amount = 0
        self.follower_index = 0
        self.c = 0
        self.from_backup: bool = from_backup
        if from_backup:
            self.__dict__ = from_pickle('follow_flow_backup.pickle')

    def __call__(self, amount_to_follow: int = 5000):
        print('following')
        print('followed already %s' % self.followed_amount)
        while self.followed_amount <= amount_to_follow:
            to_pickle(self.__dict__, 'follow_flow_backup.pickle')
            self.follower = self.targets[self.follower_index]
            self.follower_index += 1
            self.target = client.client.user_info_by_username_v1(self.follower)
            if not self.target.is_private and self.target.media_count > 10 \
                    and 4000 >= self.target.follower_count >= 400 \
                    and 1000 >= self.target.following_count >= 100:
                self.client.follow(self.target.pk)
                with sqlite3.connect('followed.db') as con:
                    con.execute('insert into followed (username) values (?)', (self.target.username,))
                    con.commit()
                self.followed_amount += 1
                self.c += 1
                print('followed %s' % self.target.username, self.target.follower_count, self.target.following_count)
                now = datetime.now()
                son_na_12_chasov = self.followed_amount % 400 == 0
                if son_na_12_chasov:
                    sleep_amount = 60 * 60 * 12
                    sleep_info = f'next iter would be at {now + timedelta(hours=12)}', 'son na 12 chasov'
                    self.c = 0
                    print(sleep_info, self.followed_amount)
                    sleep(sleep_amount)
                elif self.c % 60 == 0 and not son_na_12_chasov:
                    sleep_amount = 60 * 60
                    sleep_info = f'next iter would be at {now + timedelta(hours=1)}', 'son na 1 chas'
                    self.c = 0
                    print(sleep_info, self.followed_amount)
                    sleep(sleep_amount)


def targets(client: ClientInterface, target: str, target_parse_amount: int = 0, from_backup: bool = False):
    pool = ThreadPool(processes=2)
    if from_backup:
        followers = from_pickle(f'{target}_followers.pickle')
        my_followings = from_pickle('my_followings.pickle')
    else:
        async_result = pool.apply_async(client.collect_followings, args=(client.username,))
        async_result_2 = pool.apply_async(client.collect_followers, args=(target, target_parse_amount))
        my_followings = set(user.username for user in async_result.get())
        followers = set(user.username for user in async_result_2.get()[0])
        to_pickle(my_followings, 'my_followings.pickle')
        to_pickle(followers, f'{target}_followers.pickle')
    with sqlite3.connect('followed.db') as con:
        followed_db = {i[0] for i in con.execute('select username from followed').fetchall()}
    non_followed = [i for i in followers - followed_db - my_followings]
    return non_followed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=str, required=True)
    parser.add_argument('-a', '--amount', type=int, default=5000)
    parser.add_argument('--from_backup', type=bool, default=False)
    args = parser.parse_args()
    target = args.target
    username, password = ('alexey_naidiuk', 'Zxcvasdfqwer1234')
    with ClientInterface(username, password) as client:
        client.login()
        targets_list = targets(client, target, 0, from_backup=args.from_backup)
        follow = Follow(client, targets_list, from_backup=args.from_backup)
        follow(args.amount)
