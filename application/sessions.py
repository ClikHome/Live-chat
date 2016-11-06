#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.gen
import tornadoredis


class RedisSessionStore:
    def __init__(self, redis_connection, **options):
        self.options = {
            'expire': 60 * 60,
            'key_prefix': 'session'
        }
        self.options.update(options)
        # self.redis = redis_connection
        self.redis = tornadoredis.Client()

    def redis_link(self, sid):
        return '{}:{}'.format(self.options['key_prefix'], sid)

    @tornado.gen.engine
    def get(self, session_id):
        result = yield tornado.gen.Task(self.redis.get, self.redis_link)

    def __getitem__(self, item):
        pass

