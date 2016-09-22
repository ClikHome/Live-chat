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

from datetime import datetime, timedelta
from tornado.httpserver import HTTPServer

from config import *


class ChatConnection(sockjs.tornado.SockJSConnection):
    connections = {}
    messages_history = {}
    cookies = {}

    authenticated = False
    token = None
    username = None
    cookie = None
    timedelta = None

    def send_error(self, message, error_type=None):
        return self.send(json.dumps({
            'data_type': 'error' if not error_type else '%s_error' % error_type,
            'data': {
                'message': message
            }
        }))

    def send_message(self, message, data_type):
        return self.send(json.dumps({
            'data_type': data_type,
            'data': message,
        }))

    def on_open(self, info):
        self.cookie = info.get_cookie('sessionid').value

        if self.cookie in self.cookies:
            self.username = self.cookies[self.cookie]['username']
            self.token = self.cookies[self.cookie]['token']

            self.authenticated = True
            self.connections.setdefault(self.token, {})[self.username] = self

            self.send(json.dumps({
                'data_type': 'auth_success',
                'username': self.username
            }))

            logging.debug(
                "Client authenticated: token '%s', name '%s'" % (self.token, self.username))
        logging.debug('Connection was opened!')

    @tornado.gen.coroutine
    def on_message(self, msg):
        logging.debug('-' * 20)
        logging.debug('Got message: ' + str(msg))
        logging.debug('Active user: {"token": "%s", "username": "%s", "authorized": "%s"}' % (
            self.token, self.username, self.authenticated))

        try:
            message = json.loads(msg)
        except ValueError:
            self.send_error("Invalid JSON")
            logging.debug("Invalid JSON")
            return

        if message['data_type'] == 'auth' and not self.authenticated:
            self.token = message.get('token', None)
            self.username = message.get('username', None)

            if self.token and self.username:
                if self.username in self.connections.get(self.token, {}):
                    self.send({'data_type': 'username_already_taken'})
                    return

                self.authenticated = True
                self.connections.setdefault(self.token, {})[self.username] = self

                self.cookies[self.cookie] = {
                    'username': self.username,
                    'token': self.token
                }

                self.send(json.dumps({
                    'data_type': 'auth_success',
                    'username': self.username
                }))

                logging.debug(
                    "Client authenticated: token '%s', name '%s'" % (self.token, self.username))

        elif message['data_type'] == 'get_history' and message.get('token') and message.get('timezone'):
            self.token = message['token']
            self.timedelta = datetime.fromtimestamp(
                message['timezone']) - datetime.utcfromtimestamp(message['timezone'])

            history_to_token = []
            chat_history = self.messages_history.get(self.token, [])

            for single_message in chat_history:
                single_message['time'] = self.get_local_time(single_message['datetime'])
                history_to_token.append({key: value for key, value in single_message.items() if key != 'datetime'})

            self.send(json.dumps({'data_type': 'history', 'messages': history_to_token}))

        elif message['data_type'] == 'message' and self.authenticated and self.token and self.username:
            data = {
                'data_type': 'message',
                'message': message['body'],
                'username': self.username,
                'time': self.local_time
            }

            for name, connection in self.connections[self.token].items():
                connection.send(json.dumps(data))

            data['datetime'] = datetime.utcnow()
            del data['data_type']
            self.messages_history.setdefault(self.token, []).append(data)

            logging.debug('Message was sent!')

        else:
            self.send_error("Invalid data type %s" % message['data_type'])
            logging.debug("Invalid data type %s" % message['data_type'])

    def on_close(self):
        if self.connections.get(self.token) and self.connections[self.token].get(self.username):
            del self.connections[self.token][self.username]
        logging.debug("Client was removed: token '%s', name '%s'" % (self.token, self.username))

        return super(ChatConnection, self).on_close()

    @property
    def local_time(self):
        if self.timedelta:
            return self.get_local_time(datetime.utcnow())
        return None

    def get_local_time(self, utc_datetime):
        if utc_datetime:
            return (utc_datetime + self.timedelta).time().strftime('%H:%M')
        return None

    @property
    def is_valid(self):
        return all([self.authenticated, self.token, self.timedelta, self.username])



