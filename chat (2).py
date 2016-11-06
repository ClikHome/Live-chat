# -*- coding: utf-8 -*-
# !/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.autoreload
import json
import sockjs.tornado
import logging
import tornadoredis
import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream

from datetime import datetime, timedelta
from tornado.ioloop import IOLoop
from tornado import gen

from config import *
from application.users import UsersRedisStore
from application.redis_keys import RedisKeys

# Templates of Redis keys
keys = RedisKeys()

# Install ZMQ ioloop instead of a tornado ioloop
ioloop.install()


class ChatConnection(sockjs.tornado.SockJSConnection):
    connections = {}

    # Redis store
    users_store = UsersRedisStore(
        'channel_id', 'username', 'ip')

    # Redis client
    rclient = tornadoredis.Client()
    rclient.connect()

    # ZeroMQ
    context = zmq.Context()
    publisher = context.socket(zmq.PAIR)
    publisher.bind("tcp://127.0.0.1:5557")
    publish_stream = ZMQStream(publisher)

    def __init__(self, session):
        super(ChatConnection, self).__init__(session)

        self.authenticated = False
        self.channel = None
        self.channel_id = None
        self.username = None
        self.session_id = None
        self.ip = None

        self.uploaded_messages_count = 0

    def send_error(self, message, error_type=None):
        return self.send(json.dumps({
            'data_type': 'error' if not error_type else '%s_error' % error_type,
            'data': {
                'message': message
            }
        }))

    def send_message_to_channel(self, message):
        message = json.dumps({
            'data_type': 'message',
            'data': message
        })

        self.broadcast(self.connections.get(self.channel_id, []), message)

    def send_message(self, user, body, created_at):
        return self.send(json.dumps({
            'data_type': 'message',
            'data': {
                'body': body,
                'user': user,
                'datetime': created_at
            }
        }))

    @gen.engine
    def send_history(self, start, finish, data_type='history'):
        history_to_channel = []

        with self.rclient.pipeline() as pipe:
            pipe.lrange('channel:{}:messages'.format(self.channel), -finish, -start)
            result = yield tornado.gen.Task(pipe.execute)

            if isinstance(result, list) and result:
                for history_message in map(json.loads, result[0]):
                    # history_message['time'] = self.get_local_time(history_message['datetime'])
                    history_to_channel.append(history_message)

        self.send(json.dumps({'data_type': data_type, 'messages': history_to_channel}))
        self.uploaded_messages_count += len(history_to_channel)

    def set_cookie(self, key, value, path='/', expires=60*60*24*30):
        self.send(json.dumps({
            'data_type': 'set_cookie',
            'key': key,
            'value': value,
            'path': path,
            'expires': expires
        }))

    @gen.engine
    def on_open(self, info):
        expiry_date = self.session.__dict__['expiry_date']
        logging.debug('Session expiry: ' + str(datetime.fromtimestamp(expiry_date)))

        self.ip = info.ip
        session_id = info.get_cookie('sessionid')
        self.session_id = session_id.value if session_id else None

        if self.session_id:
            session = yield self.users_store.get_session(self)
            logging.debug('Got session: ' + str(session))

            if session:
                user = yield self.users_store.load_user(self, session)
                logging.debug('Got user: ' + str(user))
                self.login_as(user)

        logging.debug('Connection was opened!')

    @gen.engine
    def on_message(self, msg):
        logging.debug('-' * 20)

        # logging.debug(u'Got message: ' + str(unicode(msg).encode('utf-8')))

        try:
            message = json.loads(msg)
        except ValueError:
            self.send_error("Invalid JSON")
            logging.debug("Invalid JSON")
            return

        # Authorization
        if message['data_type'] == 'auth' and not self.authenticated:
            self.channel = message.get('channel', None)
            self.username = message.get('username', '').strip().title()

            if self.channel and self.username:
                # Checking channel in Redis
                result = yield tornado.gen.Task(
                    self.rclient.hget, 'channels', self.channel)

                if not result or (not result.isdigit() and not isinstance(result, int)):
                    self.send_error('Channel not valid', error_type='auth')
                    return

                self.channel_id = int(result)

                # # Check if username already used
                # channel_used_usernames = yield gen.Task(
                #     self.rclient.smembers, keys.channel_users(self.channel)
                # )
                #
                # if self.username in channel_used_usernames:
                #     self.send_error('Username is used', error_type='auth')

                # User login if user already exist else create user
                if not self.authenticated:
                    # Register new user
                    yield self.users_store.set_user(self)
                    yield self.users_store.set_session(self, 60)

                    # Send data to Django
                    # if self.is_valid:


                self.login_as({
                    'username': self.username,
                    'channel': self.channel,
                })

                self.publish_stream.send_json({
                    'data_type': 'user',
                    'data': {
                        'username': self.username,
                        'channel_id': self.channel_id,
                        'created_at': datetime.utcnow().strftime(
                            MESSAGES_DATETIME_FORMAT),
                        'ip': self.ip,
                    }
                })

        elif message['data_type'] == 'load_more_history':
            self.send_history(
                self.uploaded_messages_count,
                self.uploaded_messages_count + HISTORY_MESSAGES_TO_LOAD,
                data_type='more_history')

        # Messages
        elif message['data_type'] == 'message' and self.is_valid:
            received_message = {
                'data_type': 'message',
                'data': {
                    'body': message['body'],
                    'channel_id': int(self.channel_id),
                    'username': self.username,
                    'created_at': datetime.utcnow().strftime(MESSAGES_DATETIME_FORMAT)
                }
            }

            # Send message to all users of chat
            self.send_message_to_channel(received_message['data'])

            # Send message to Django
            self.publish_stream.send_json(received_message)

            # result = yield tornado.gen.Task(
            #     self.rclient.rpush, 'channel:{}:messages'.format(self.channel), json.dumps(_message))

            # Update last activity of user
            # yield self.users_store.last_activity(self)

            self.uploaded_messages_count += 1
            logging.debug('Message was sent!')

        else:
            self.send_error("Invalid data type %s" % message['data_type'])
            logging.debug("Invalid data type %s" % message['data_type'])

    def on_close(self):
        if self.is_valid:
            self.connections[self.channel_id].remove(self)

        # Properly close ZMQ sockets
        # self.publish_stream.close()

        logging.debug("Client was removed: channel '%s', name '%s'" % (
            self.channel_id, self.username))

    def login_as(self, data):
        if not data.get('username', None) and not data.get('channel', None):
            logging.info('Got user without required parameters: ' + str(data))
            return

        for key, value in data.items():
            if key in self.users_store.fields:
                if key not in ['ip']:
                    setattr(self, key, value)

        self.authenticated = True
        self.connections.setdefault(self.channel_id, set()).add(self)

        self.send(json.dumps({
            'data_type': 'auth_success',
            'username': self.username
        }))

        logging.debug(
            "Client authenticated: channel '%s', name '%s'" % (
                self.channel_id, self.username))

    @property
    def is_valid(self):
        return all([self.authenticated, self.channel, self.username])

    @classmethod
    def dump_stats(cls):
        connections = sum([len(cls.connections[channel]) for channel in cls.connections])
        logging.info('Clients: ' + str(connections))

    def __getitem__(self, item):
        return getattr(self, item)


