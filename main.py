import json
import pickle
import time
from datetime import datetime, timedelta
from typing import Any

from instagrapi import Client


class ClientInterface:

    def __init__(self, username: str, password: str, device: dict = None):
        self.username, self.password, self.device = username, password, device
        self.client = Client()

    def login(self) -> bool:
        self.set_settings()
        return self.client.login(self.username, self.password)

    def set_settings(self) -> None:
        if self.device:
            self.client.set_settings(self.device)

    def dump_settings(self) -> None:
        with open('device.json', 'w') as file:
            json.dump(self.client.get_settings(), file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.dump_settings()

    def collect_followers(self, target_username: str, amount: int = 0) -> tuple:  # 20 sec amount = 6921
        print('collecting followers of %s' % target_username)
        target_user_id = self.client.user_id_from_username(target_username)
        followers_id = self.client.user_followers_v1_chunk(target_user_id, max_amount=amount)  # id
        return followers_id

    def collect_followings(self, target_username: str):
        print('collecting followings of %s' % target_username)
        target_user_id = self.client.user_id_from_username(target_username)
        followings = self.client.user_following_v1(target_user_id)
        return followings

    def follow(self, target_id: str):
        self.client.user_follow(target_id)


def to_pickle(data: Any, file_name):
    with open(file_name, 'wb') as file:
        pickle.dump(data, file)


def from_pickle(file_name: str):
    with open(file_name, 'rb') as file:
        data = pickle.load(file)
    return data


class Main:

    def __init__(self, client: ClientInterface, target: str, from_backup: bool = False):
        self.c = 0
        self.follower_index = 0
        self.client = client
        if from_backup:
            self.__dict__ = from_pickle('backup.pickle')
        else:
            self.my_followings = self.client.collect_followings(client.username)  # todo parallelized
            self.followers = self.client.collect_followers(target, 4000)[0]  # todo parallelized
            self.non_followed = set(i.pk for i in self.followers) - set(i.pk for i in self.my_followings)
            self.iterable_followers = iter(self.non_followed)

    def __call__(self, amount: int = 300, timeout: int = 30):
        while self.c < amount:
            to_pickle(self.__dict__, 'backup.pickle')
            if self.c % 50 == 0 and not self.c == amount:
                now = datetime.now()
                print(f'next iter would be at {now + timedelta(minutes=timeout)}')
                time.sleep(60 * timeout)
            self.follower = self.followers[self.follower_index]
            self.follower_index += 1
            if self.follower.is_private:
                continue
            self.target_info = client.client.user_info_v1(self.follower.pk)
            if self.target_info.media_count > 10 \
                    and 4000 >= self.target_info.follower_count >= 400 \
                    and 1000 >= self.target_info.following_count >= 100:
                self.client.follow(self.target_info.pk)
                self.c += 1
                print(self.target_info)
                print('followed %s' % self.c)
                yield self.target_info


if __name__ == '__main__':
    username, password = ('alexey_naidiuk', 'Zxcvasdfqwer1234')
    device = json.load(open('device.json'))
    with ClientInterface(username, password, device) as client:
        client.login()
        main = Main(client, 'slavakononovofficial')
        main(500)
