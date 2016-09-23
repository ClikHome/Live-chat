# -*- coding: utf-8 -*-
# !/usr/bin/env python

import sockjs.tornado
import tornado.web
import tornado.ioloop
import logging
import sys

from config import *
from chat import ChatConnection


if __name__ == "__main__":
    #   Logging application
    logging.getLogger().setLevel(logging.DEBUG)

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format=LOGGING_LINE_FORMAT,
        datefmt=LOGGING_DATETIME_FORMAT
    )

    #   Create chat router
    ChatRouter = sockjs.tornado.SockJSRouter(ChatConnection, '/echo')

    #   Create Tornado application
    application = tornado.web.Application(ChatRouter.urls, debug=True)
    application.listen(PORT, no_keep_alive=True)

    ioloop = tornado.ioloop.IOLoop.instance()

    #   Print current host and port
    logging.info('Tornado app listen on http://{host}:{port}'.format(host=HOST, port=PORT))

    ioloop.start()