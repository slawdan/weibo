# -*- coding: utf-8 -*-

"""
Python sina weibo sdk.

Rely on `requests` to do the dirty work, so it's much simpler and cleaner
than the official SDK.

For more info, refer to:
http://lxyu.github.com/weibo/
"""

import json
import time
import urllib

import requests


class Client(object):
    def __init__(self, api_key, api_secret, redirect_uri, uid=None,
                 access_token=None, expires_at=None):
        # const define
        self.site = 'https://api.weibo.com/'
        self.authorization_url = self.site + 'oauth2/authorize'
        self.token_url = self.site + 'oauth2/access_token'
        self.api_url = self.site + '2/'

        # init basic info
        self.client_id = api_key
        self.client_secret = api_secret
        self.redirect_uri = redirect_uri
        self.uid = uid
        self.access_token = access_token
        self.expires_at = expires_at
        self.session = None

        # activate client directly if given acccess_token and expires_at
        if access_token and expires_at:
            self.set_token(access_token, expires_at)

    @property
    def authorize_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri
        }
        return '%s?%s' % (self.authorization_url, urllib.urlencode(params))

    @property
    def token_info(self):
        """
        This token_info can be stored to directly activate client at next time.
        """
        return {
            'uid': self.uid,
            'access_token': self.access_token,
            'expires_at': self.expires_at
        }

    @property
    def alive(self):
        if self.expires_at:
            return self.expires_at > time.time()
        else:
            return False

    def set_code(self, authorization_code):
        """
        Activate client by authorization_code.
        """
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }
        response = requests.post(self.token_url, data=params)
        tk = json.loads(response.content)

        self._assert_error(tk)
        self.set_token(tk['access_token'], time.time() + int(tk['expires_in']))

    def set_token(self, access_token, expires_at):
        """
        Directly activate client by access_token.
        """
        self.access_token = access_token
        self.expires_at = expires_at
        self.session = requests.session()
        self.session.params = {'access_token': self.access_token}

    def _assert_error(self, d):
        if 'error_code' in d and 'error' in d:
            raise RuntimeError("[%s] %s" % (d['error_code'], d['error']))

    def get(self, uri, **kwargs):
        """
        Request resource by get method.
        """
        url = "%s%s.json" % (self.api_url, uri)
        res = json.loads(self.session.get(url, params=kwargs).text)
        self._assert_error(res)
        return res

    def post(self, uri, **kwargs):
        """
        Request resource by post method.
        If there is a 'pic' field, it accept a string, a list/tuple, or a
        file-like object as value. 
        If the value is 
            a string: requests will use 'pic' as file name
            a file-like object: requests will use the file's name
            a list/tuple: request will use the tuple[0] as file name,
                          tuple[1] as file content string/file-like object,
                          tuple[2] as mime type
        Examples:
            client.post('statuses/upload', pic='content of a pic')
            client.post('statuses/upload', pic=open('foo.jpg', 'r'))
            client.post('statuses/upload', pic=('foo.jpg', 'pic content'))
            client.post('statuses/upload', pic=('foo.jpg', open('foo.jpg', 'r')))
            client.post(
                'statuses/upload', 
                pic=('foo.jpg', 'pic content', 'image/jpeg')
                )
            client.post(
                'status/upload', 
                pic=('foo.jpg', open('foo.jpg', 'r'), 'image/jpeg')
                )
        """
        url = "%s%s.json" % (self.api_url, uri)
        pic = kwargs.pop('pic', None)
        res = json.loads(self.session.post(
            url, 
            data=kwargs, 
            files={'pic': pic} if pic else None
            ).text)
        self._assert_error(res)
        return res
