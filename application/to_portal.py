#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import gen
from tornado.ioloop import IOLoop
import momoko
import psycopg2
import json
import logging

from config import *

logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.DEBUG,
    format=LOGGING_LINE_FORMAT,
    datefmt=LOGGING_DATETIME_FORMAT
)


def dns(**options):
    string = ''

    for key, value in options.items():
        string += '{key}={value} '.format(key=key, value=value)

    return string.strip()


class CacheToPostgresql(object):
    def __init__(self):
        self.db = None

    def dns(self, **options):
        return 'dbname={db_name} user={user} password={password} host={host} ' \
               'port={port}'.format(**options)

    def test(self):
        print self.__dict__

    @gen.coroutine
    def cache_message(self): # , body, created_at, is_active, channel_id, user_id):
        cursor = yield self.db.execute("SELECT 1;")
        cursor.fetchone()


@gen.coroutine
def save_message_to_portal(message):
    if not isinstance(message, (str, unicode)):
        message = json.dumps(message)

    try:
        pass

    except (psycopg2.Warning, psycopg2.Error) as error:
        logging.warning(str(error))


if __name__ == '__main__':
    ioloop = IOLoop.instance()
    caching = CacheToPostgresql()

    caching.db = momoko.Pool(
        dsn=dns(
            db_name='live_chat',
            user='eugene',
            password='qwerty123',
            host='localhost',
            port=5432
        ),
        size=1,
        max_size=3,
        ioloop=ioloop,
        raise_connect_errors=False,
    )

    ioloop.start()

    # future = cacher.db.connect()
    # ioloop.add_future(future, lambda f: ioloop.stop())
    # ioloop.start()
    # future.result()




