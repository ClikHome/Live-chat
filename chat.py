# -*- coding: utf-8 -*-
# !/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.autoreload
import sys
import json
import sockjs.tornado
import logging
import tornadoredis
import uuid

from datetime import datetime, timedelta
from tornado.ioloop import IOLoop
from sockjs.tornado.sessioncontainer import SessionContainer

from config import *


class ChatConnection(sockjs.tornado.SockJSConnection):
    connections = {}
    cookies = {}
    sessions = {}


    # Settings of user
    authenticated = False
    channel = None
    username = None
    session_id = None
    timedelta = None
    uploaded_messages_count = 0

    # Redis client
    rclient = tornadoredis.Client()
    rclient.connect()

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
            'data': {
                'body': message,
                'user': self.username,
                'time': datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')
            }
        })

        self.broadcast(self.connections.get(self.channel, []), message)

    def send_message(self, user, body, created_at):
        return self.send(json.dumps({
            'data_type': 'message',
            'data': {
                'body': body,
                'user': user,
                'time': created_at
            }
        }))

    @tornado.gen.engine
    def send_history(self, start, finish, data_type='history'):
        history_to_channel = []

        with self.rclient.pipeline() as pipe:
            pipe.lrange('channel:{}:messages'.format(self.channel), -finish, -start)
            result = yield tornado.gen.Task(pipe.execute)

            if isinstance(result, list) and result:
                for history_message in map(json.loads, result[0]):
                    history_message['time'] = self.get_local_time(history_message['datetime'])
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

    @tornado.gen.engine
    def on_open(self, info):

        logging.info('New client at %s' % str(info.__dict__))

        self.session_id = info.get_cookie('sessionid')
        self.session_id = self.session_id.value if self.session_id else None

        # result = yield tornado.gen.Task(self.rclient.exists, 'channel:{}:users'.format(self.channel), self.uid)
        # logging.debug('Result of saving user to Redis: ' + str(result))

        if self.session_id and self.session_id in self.sessions:
            user_data = self.sessions[self.session_id]
            self.sign_in_like(user_data['username'], user_data['channel'])






        logging.debug('Connection was opened!')

    # @tornado.web.asynchronous
    @tornado.gen.engine
    def on_message(self, msg):
        logging.debug('-' * 20)
        logging.debug('Got message: ' + str(msg))

        try:
            message = json.loads(msg)
        except ValueError:
            self.send_error("Invalid JSON")
            logging.debug("Invalid JSON")
            return

        # Authorization
        if message['data_type'] == 'auth' and not self.authenticated:
            self.channel = message.get('channel', None)
            self.username = message.get('username', None)

            if self.channel and self.username:
                for user in self.connections.get(self.channel, []):
                    if user.username == self.username and id(user) != id(self):
                        return

                    # Save session to Redis
                    # with self.rclient.pipeline() as pipe:
                    #     pipe.sadd('channel:{}:users'.format(self.channel), self.session_id)
                    #     user_directory = 'channel:{}:user:{}'.format(self.channel, self.session_id)
                    #     pipe.hset(user_directory, 'username', self.username)
                    #     pipe.hset(user_directory, 'channel', self.channel)
                    #
                    #     result = yield tornado.gen.Task(pipe.execute)
                    #     logging.debug('Result of saving user to Redis: ' + str(result))

                    self.sign_in_like(self.username, self.channel)

        # History
        elif message['data_type'] == 'get_history' and message.get('channel') and message.get('timezone'):
            self.channel = message['channel']
            self.timedelta = datetime.fromtimestamp(
                message['timezone']) - datetime.utcfromtimestamp(message['timezone'])

            self.send_history(1, HISTORY_MESSAGES_TO_LOAD)
            self.connections.setdefault(self.channel, set()).add(self)

        elif message['data_type'] == 'load_more_history':
            self.send_history(

                self.uploaded_messages_count,
                self.uploaded_messages_count + HISTORY_MESSAGES_TO_LOAD,
                data_type='more_history'
            )


        # Messages
        elif message['data_type'] == 'message' and self.is_valid:
            self.send_message_to_channel(message['body'])

            _message = {
                'channel': self.channel,
                'user': self.username,
                'body': message['body'],
                'datetime': datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')
            }

            result = yield tornado.gen.Task(
                self.rclient.rpush, 'channel:{}:messages'.format(self.channel), json.dumps(_message))

            self.uploaded_messages_count += 1
            logging.debug('Message was sent!')

        else:
            self.send_error("Invalid data type %s" % message['data_type'])
            logging.debug("Invalid data type %s" % message['data_type'])

    def on_close(self):
        if self.authenticated:
            self.connections[self.channel].remove(self)
        logging.debug("Client was removed: channel '%s', name '%s'" % (self.channel, self.username))

        return super(ChatConnection, self).on_close()

    def sign_in_like(self, username, channel):
        self.username = username
        self.channel = channel
        self.authenticated = True
        self.connections.setdefault(channel, set()).add(self)

        self.send(json.dumps({
            'data_type': 'auth_success',
            'username': username
        }))

        logging.debug(
            "Client authenticated: channel '%s', name '%s'" % (channel, username))

    @property
    def local_time(self):
        if self.timedelta:
            return self.get_local_time(datetime.utcnow())
        return None

    def get_local_time(self, utc_datetime):
        if utc_datetime:
            if isinstance(utc_datetime, (unicode, str)):
                utc_datetime = datetime.strptime(utc_datetime, '%d.%m.%Y %H:%M:%S')
            return (utc_datetime + self.timedelta).time().strftime('%H:%M')
        return None

    @property
    def is_valid(self):
        return all([self.authenticated, self.channel, self.timedelta, self.username])

    @classmethod
    def dump_stats(cls):
        connections = sum([len(cls.connections[channel]) for channel in cls.connections])
        logging.info('Clients: ' + str(connections))



