#!/usr/bin/python
#coding=utf8

from cStringIO import StringIO

class StrStream(object):
    def __init__(self, body):
        self.body = body
        self.pos = 0

    def read_until(self, delimiter, callback):
        """Call callback when we read the given delimiter."""
        if self.pos >= len(self.body):
            return ''
        index = self.body.find(delimiter, self.pos)
        if index == -1:
            new_pos = len(self.body)
        else:
            new_pos = index + len(delimiter)
        buffer = self.body[self.pos:new_pos]
        self.pos = new_pos
        callback(buffer)

    def read_bytes(self, num_bytes, callback):
        assert isinstance(num_bytes, (int, long))
        new_pos = self.pos + num_bytes
        buffer = self.body[self.pos:new_pos]
        self.pos = new_pos
        callback(buffer)
