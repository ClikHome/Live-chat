# !/usr/bin/env python
# -*- coding: utf-8 -*-

from motorengine.document import Document
from motorengine.fields import (
    StringField, DateTimeField, BooleanField, ReferenceField, URLField,)

class Token(Document):
    uuid = StringField(max_length=50, required=True)
    created_at = DateTimeField(auto_now_on_insert=True)
    expiry_at = DateTimeField()
    site = URLField(required=True)

    def __str__(self):
        return self.uuid



class User(Document):
    username = StringField(required=True, max_length=245)
    token = StringField(required=True, max_length=245)
    session_id = StringField(max_length=245)

    created_at = DateTimeField(auto_now_on_insert=True)
    last_activity = DateTimeField()

    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=True)

    def __str__(self):
        return self.username


class Message(Document):
    token = ReferenceField(Token)
    user = ReferenceField(User)
    body = StringField()
    datetime = DateTimeField(auto_now_on_insert=True)

    def __str__(self):
        return self.body

