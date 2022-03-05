import json
import sqlite3

from instagrapi import Client


class Data:

    def __init__(self, file_name: str = None):
        self.con = sqlite3.connect(file_name)
        self.cur = self.con.cursor()


class ClientInterface:

    def __init__(self):
        user_id, device, username, password = Data('data.db').con.execute('select * from user_data').fetchone()
        self.client = Client()
        self.client.set_device()

    def login(self):
        self.client.login(self.username, self.password)

    def set_device(self):
        if self.device:
            device = json.loads(self.device)
            self.client.set_device(device)

    def dump_device(self):
        device_dump = json.dumps(self.client.get_settings()).encode('utf-8')
        self.con.execute('update user_data set device = ? where id = ?', (device_dump, self.user_id))

    def __enter__(self):
        self.set_device()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dump_device()
