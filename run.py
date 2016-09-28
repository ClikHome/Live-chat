# -*- coding: utf-8 -*-
# !/usr/bin/env python

import sockjs.tornado
import tornado.web
import tornado.ioloop
import tornadoredis
import logging
import sys

from os import environ
from config import *
from chat import ChatConnection


if __name__ == "__main__":
    #   Logging application
    logging.getLogger().setLevel(logging.DEBUG)

    logging.basicConfig(
        level=logging.DEBUG,
        format=LOGGING_LINE_FORMAT,
        datefmt=LOGGING_DATETIME_FORMAT
    )

    #   Create chat router
    ChatRouter = sockjs.tornado.SockJSRouter(ChatConnection, '/echo')

    #   Create Tornado application
    settings = {'debug': True}
    application = tornado.web.Application(ChatRouter.urls, **settings)
    application.listen(int(os.environ.get('PORT', '5000')), no_keep_alive=True)

    # tornado.ioloop.PeriodicCallback(ChatConnection.dump_stats, 1000).start()

    ioloop = tornado.ioloop.IOLoop.instance()

    #   Print current host and port
    logging.info('Tornado app listen port on {port}'.format(port=PORT))

    ioloop.start()