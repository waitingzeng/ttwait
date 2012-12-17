#! /usr/bin/env python
#coding=utf-8
import os.path as osp
import traceback
import hashlib
import json

import redis
from pyso import pysk
from pycomm.log import log
from pycomm.core.hostconfig import ClientConfig
from pycomm.utils.dict4ini import DictIni

class AutoReportRedis(redis.Redis):
    def execute_command(self, *args, **options):
        res = redis.Redis.execute_command(self, *args, **options)
        client_report(self.connection_pool.connection_kwargs['host'], self.connection_pool.connection_kwargs['port'], 0)
        return res

class RedisCli(object):
    conf_file = None
    db = 0
    def __init__(self, conf_file=None):
        if conf_file and osp.exists(conf_file):
            self.conf_file = conf_file

        assert self.conf_file and osp.exists(self.conf_file), '%s does not exists' % self.conf_file
        self.conf = ClientConfig(self.conf_file)
        self._p = None


    def connect(self):
        if self._p:
            return True
        self.conf.reload()
        server = self.conf.get_server()
        try:
            self._p = AutoReportRedis(server.SVR_IP, server.SVR_Port, db=self.db, socket_timeout = self.conf.ClientTimeout.SockTimeout)
        except Exception, e:
            traceback.print_exc()
            log.exception('MBredis connect ERROR: %s', e)
            return None
        return True


    def get(self, key):
        try:
            self.connect()
            ret = self._p.get(key)
            if ret:
                return 0, ret
            else:
                return -1, ret
        except Exception, e:
            log.exception('get: key[%s] fail %s', key, e)
            self._p = None
        return -2, None
    __getitem__ = get


    def set(self, key, value, timeout=None):
        try:
            self.connect()
            if timeout:
                ret = self._p.setex(key, value, timeout)
            else:
                ret = self._p.set(key, value)
            if ret:
                return 0
            else:
                return -1
        except Exception, e:
            log.exception('set: key[%s] value[%s] fail', key, value)
            self._p = None
        return -2
    __setitem__ = set

    def mget(self, keys):
        try:
            self.connect()
            if not keys:
                return -3, []
            ret = self._p.mget(keys)
            if ret:
                return 0, ret
            else:
                return -1, ret
        except Exception, e:
            log.exception('mget: keys %s',  keys)
            self._p = None
        return -2, None

    def mset(self, mapping, timeout=None):
        """
        @in:    mapping
                @type:  dict
        """
        try:
            self.connect()
            ret = self._p.mset(mapping)
            if ret:
                if timeout:
                    for key in mapping.iterkeys():
                        self.expire(key, timeout)
                return 0
            else:
                return -1
        except Exception, e:
            log.exception('mset: %s fail', mapping)
            self._p = None
        return -2

    def expire(self, key, expire_time):
        """
        Set an expire flag on key ``key`` for ``time`` seconds
        """
        try:
            self.connect()
            ret = self._p.expire(key, expire_time)
            if ret:
                return 0
            else:
                return -1
        except Exception, e:
            log.error('get: %s, %s' % (e, traceback.format_exc()))
            self._p = None
        return -2

    def mttl(self, keys):
        """
        Returns the number of seconds until the key ``name`` will expire
        """
        try:
            ttls = {}
            self.connect()
            if not keys:
                return -3, {}
            for key in keys:
                ttls[key] = self._p.ttl(key)
            return 0, ttls
        except Exception, e:
            log.exception('mget: keys %s',  ','.join(keys))
            self._p = None
        return -2, {}

    def ttl(self, key):
        ret, ttls = self.mttl([key])
        return ret, ttls.get(key, None)

    
    def mhget(self, names, key):
        self.connect()
        pipe = self.pipeline()
        for name in names:
            pipe.hget(name, key)
        
        return pipe.execute()

    def mhmset(self, keys_vals):
        self.connect()
        pipe = self.pipeline()
        for pair in keys_vals.iteritems():
            pipe.hmset(pair[0], pair[1])

        return pipe.execute()

    def mhmget(self, names, keys):
        self.connect()
        pipe = self.pipeline()
        for name in names:
            pipe.hmget(name, keys)
        
        return pipe.execute()

    def __getattr__(self, name):
        self.connect()
        if hasattr(self._p, name):
            return getattr(self._p, name)
        raise AttributeError(name)

    
