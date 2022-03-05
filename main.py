import json
import sqlite3

from instagrapi import Client


class ClientInterface:

    def __init__(self):
        self.con = sqlite3.connect('data.db')
        self.cur = self.con.cursor()
        self.user_id, self.device, self.username, self.password = \
            self.cur.execute('select * from user_data').fetchone()
        self.client = Client()

    def login(self):
        self.client.set_device()
        self.client.login(self.username, self.password)

    def set_device(self):
        if self.device:
            device = json.loads(self.device)
            self.client.set_device(device)

    def dump_device(self):
        device_dump = json.dumps(self.client.get_settings())
        self.cur.execute('update user_data set device = ? where id = ?', (device_dump, self.user_id))
        self.con.commit()

    def __enter__(self):
        self.set_device()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dump_device()


if __name__ == '__main__':
    with ClientInterface() as client:
        client.login()
