#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import gen
from tornado.ioloop import IOLoop
from datetime import datetime
import tornadoredis
import json
import random
import redis
import logging
import tornado

from redis_keys import RedisKeys

keys = RedisKeys()

CONNECTION_POOL = tornadoredis.ConnectionPool(max_connections=500,
                                              wait_for_available=True)


class UsersRedisStore(object):
    """
    User instance must have channel and username params

    class call like this:

    store = UsersRedisStore('channel', 'username', 'ip')
    users = yield store.load_user(self)

    """
    def __init__(self, *fields):
        self.fields = fields

        # Redis connection
        self.r = tornadoredis.Client()
        self.r.connect()

    @gen.coroutine
    def load_user(self, conn, link=None):
        user_redis_link = link if link else self._user_link(conn)
        response = yield gen.Task(self.r.hgetall, user_redis_link)
        raise gen.Return(response)

    @gen.coroutine
    @gen.engine
    def set_user(self, conn):
        with self.r.pipeline() as pipe:
            user_link = keys.user(conn.channel, conn.username)

            # Create user
            for field in self.fields:
                pipe.hset(user_link, field, conn[field])
            pipe.hset(user_link, 'created_at', datetime.utcnow())

            # Add user to user list
            pipe.sadd(keys.channel_users(conn.channel), conn.username)

            yield gen.Task(pipe.execute)
        logging.info('User "{}" was saved!'.format(conn.username))

    @gen.coroutine
    def channel_users(self, conn):
        usernames = yield gen.Task(r.lrange, keys.channel_users(conn.channel), 0, -1)
        raise gen.Return(usernames)

    @gen.coroutine
    @gen.engine
    def last_activity(self, conn):
        with self.r.pipeline() as pipe:
            pipe.hset(self._user_link(conn), 'last_activity', datetime.utcnow())
            if conn.ip:
                pipe.hset(self._user_link(conn), 'ip', conn.ip)

            yield gen.Task(pipe.execute)

    @gen.coroutine
    def get_session(self, conn):
        response = yield gen.Task(
            self.r.get, keys.session(conn.session_id)
        )
        raise gen.Return(response)

    @gen.coroutine
    def set_session(self, conn, time):
        yield gen.Task(
            self.r.setex, keys.session(conn.session_id), time, self._user_link(conn)
        )

    def get_or_create_session(self, conn):
        pass

    @staticmethod
    def _user_link(conn):
        return keys.user(conn.channel_id, conn.username)


class FakeUser:
    def __init__(self):
        self.channel = 'qwerty123'
        self.username = 'eugene'
        self.ip = '125.0.0.1'

    def __getitem__(self, item):
        return getattr(self, item)


if __name__ == '__main__':
    # ioloop = IOLoop.instance()
    # store = UsersRedisStore('channel', 'username', 'ip')
    fake_user = FakeUser()
    r = redis.Redis()
    ra = tornadoredis.Client()
    ra.connect()

    # Test

    # @gen.coroutine

    @gen.engine
    def test():
        conn = fake_user
        response = yield gen.Task(
            ra.hgetall, keys.user(conn.channel, conn.username))

        print response

    tornado.gen.convert_yielded(test())
    print ra.keys()
    print ra.hgetall(keys.user(fake_user.channel, fake_user.username))

    # print 'Sync redis: ' + str(
    #     r.hgetall(keys.user(fake_user.channel, fake_user.username)))


