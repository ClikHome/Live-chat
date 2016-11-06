#!/usr/bin/env python
# -*- coding: utf-8 -*-

from method_args import ValidateArguments

validation = ValidateArguments(
    username=lambda x: x.strip().lower().replace(' ', '_'),
)


@validation
class RedisKeys:
    def channels(self):
        """
        Channels list

        :type:   <hash>
        :return: { uid : id, ... }
        """
        return 'channels'

    def user(self, channel_id, username):
        """
        User data

        :type:   <hash>
        :return: { type_user_data: data, ... }
        """
        return 'channel:{channel_id}:user:{username}'.format(**locals())

    def channel_messages(self, channel_id):
        """
        Messages of channel

        :type:   <list>
        :return: [ message_as_json, ... ]
        """
        return 'channel:{channel_id}:messages'.format(**locals())

    def session(self, session_id):
        """
        Key to session of user with expire time

        :type:   <setex>
        :return: Link to user
        """
        return 'session:{session_id}'.format(**locals())

    def channel_users(self, channel_id):
        """
        Username list of channel by channel_id

        :type:   <list>
        :return: List of used usernames
        """
        return 'channel:{channel_id}:users'.format(**locals())

    #
    # def(self):
    #     """
    #
    #
    #     :type:
    #     :return:
    #     """
    #     return ''


