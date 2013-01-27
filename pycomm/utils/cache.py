#!/usr/bin/python
#coding=utf8
import os
import hashlib



class SimpleFileBasedCache(object):
    default_ext = '.jpg'
    def __init__(self, dir, default_ext=''):
        self._dir = dir
        if default_ext:
            self.default_ext = default_ext
        if not os.path.exists(self._dir):
            self._createdir()

    def add(self, key, value):
        self.set(key, value)
        return True

    def get(self, key, default=None):
        
        fname = self._key_to_file(key)
        try:
            with open(fname, 'rb') as f:
                return f.read()
        except (IOError, OSError, EOFError):
            pass
        return default

    def set(self, key, value):
        fname = self._key_to_file(key)
        dirname = os.path.dirname(fname)

        try:
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            with open(fname, 'wb') as f:
                f.write(value)
        except (IOError, OSError):
            pass
        return fname

    def has_key(self, key):
        fname = self._key_to_file(key)
        return os.path.exists(fname)

    @classmethod
    def name_to_key(self, key, default_ext=None):
        if not default_ext:
            default_ext = self.default_ext
        path = hashlib.md5(key).hexdigest()
        path = os.path.join(path[:2], path[2:4], path[4:])
        return path + default_ext

    def _createdir(self):
        try:
            os.makedirs(self._dir)
        except OSError:
            raise EnvironmentError("Cache directory '%s' does not exist and could not be created'" % self._dir)

    def __contains__(self, key):
        """
        Returns True if the key is in the cache and has not expired.
        """
        # This is a separate method, rather than just a copy of has_key(),
        # so that it always has the same functionality as has_key(), even
        # if a subclass overrides it.
        return self.has_key(key)

    def _key_to_file(self, key):
        path = self.name_to_key(key)
        return os.path.join(self._dir, path)
