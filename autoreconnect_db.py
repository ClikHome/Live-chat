# -*- coding: utf-8 -*-
# !/usr/bin/env python

import momoko
import psycopg2
import tornado.autoreload
import tornado.gen
import tornado.web


@tornado.gen.coroutine
def reload_if_db_pool_is_dead(db):
    """
        Restart application if database connection is dead.
        It help to solve psycopg2 bug. To date, It's the most adequate and reliable solution.
    """
    try:
        cursor = yield db.execute('SELECT 1')
        cursor.fetchall()
    except (psycopg2.OperationalError, psycopg2.ProgrammingError, momoko.connection.Pool.DatabaseNotAvailable):
        tornado.autoreload._reload()