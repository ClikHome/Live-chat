# -*- coding: utf-8 -*-
# !/usr/bin/env python

import os

PORT = 5000


# Logging
LOGGING_LINE_FORMAT = 'LINE:%(lineno)d [%(filename)s] #%(levelname)-2s [%(asctime)s] %(message)s'
LOGGING_DATETIME_FORMAT = '%m/%d/%Y %H:%M:%S'

# Pathes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

# Chat settings
HISTORY_MESSAGES_TO_LOAD = 10
MESSAGES_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

REDIS_DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"

# ZeroMQ
ZERO_MQ_PORT = 5556
IPC_SOCKET = lambda x: "tcp://127.0.0.1:%d" % x


