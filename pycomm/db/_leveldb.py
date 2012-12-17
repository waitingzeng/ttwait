#!/usr/bin/env python
#
# Copyright (C) 2012 Space Monkey, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
    LevelDB Python interface via C-Types.
    http://code.google.com/p/leveldb-py/

    Missing still (but in progress):
      * snapshots
      * custom comparators, filter policies, caches

    This isn't exactly the most performant interface to LevelDB, but this
    interface requires nothing more than the leveldb shared object with the C
    api being installed.

    There's a bug with LevelDB 1.5's build script that may make getting this
    to work challenging for you. See:
    http://code.google.com/p/leveldb/issues/detail?id=94
"""

__author__ = "JT Olds"
__email__ = "jt@spacemonkey.com"

import ctypes
import ctypes.util
import weakref
from collections import namedtuple

_ldb = ctypes.CDLL(ctypes.util.find_library('leveldb'))
_libc = ctypes.CDLL(ctypes.util.find_library('c'))

_ldb.leveldb_filterpolicy_create_bloom.argtypes = [ctypes.c_int]
_ldb.leveldb_filterpolicy_create_bloom.restype = ctypes.c_void_p
_ldb.leveldb_filterpolicy_destroy.argtypes = [ctypes.c_void_p]
_ldb.leveldb_cache_create_lru.argtypes = [ctypes.c_size_t]
_ldb.leveldb_cache_create_lru.restype = ctypes.c_void_p
_ldb.leveldb_cache_destroy.argtypes = [ctypes.c_void_p]

_ldb.leveldb_options_create.argtypes = []
_ldb.leveldb_options_create.restype = ctypes.c_void_p
_ldb.leveldb_options_set_filter_policy.argtypes = [ctypes.c_void_p,
        ctypes.c_void_p]
_ldb.leveldb_options_set_create_if_missing.argtypes = [ctypes.c_void_p,
        ctypes.c_ubyte]
_ldb.leveldb_options_set_error_if_exists.argtypes = [ctypes.c_void_p,
        ctypes.c_ubyte]
_ldb.leveldb_options_set_paranoid_checks.argtypes = [ctypes.c_void_p,
        ctypes.c_ubyte]
_ldb.leveldb_options_set_write_buffer_size.argtypes = [ctypes.c_void_p,
        ctypes.c_size_t]
_ldb.leveldb_options_set_max_open_files.argtypes = [ctypes.c_void_p,
        ctypes.c_int]
_ldb.leveldb_options_set_cache.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_ldb.leveldb_options_set_block_size.argtypes = [ctypes.c_void_p,
        ctypes.c_size_t]
_ldb.leveldb_options_destroy.argtypes = [ctypes.c_void_p]

_ldb.leveldb_open.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
        ctypes.c_void_p]
_ldb.leveldb_open.restype = ctypes.c_void_p
_ldb.leveldb_close.argtypes = [ctypes.c_void_p]
_ldb.leveldb_put.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_void_p]
_ldb.leveldb_delete.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
_ldb.leveldb_get.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p]
_ldb.leveldb_get.restype = ctypes.POINTER(ctypes.c_char)

_ldb.leveldb_writeoptions_create.argtypes = []
_ldb.leveldb_writeoptions_create.restype = ctypes.c_void_p
_ldb.leveldb_writeoptions_destroy.argtypes = [ctypes.c_void_p]
_ldb.leveldb_writeoptions_set_sync.argtypes = [ctypes.c_void_p,
        ctypes.c_ubyte]

_ldb.leveldb_readoptions_create.argtypes = []
_ldb.leveldb_readoptions_create.restype = ctypes.c_void_p
_ldb.leveldb_readoptions_destroy.argtypes = [ctypes.c_void_p]
_ldb.leveldb_readoptions_set_verify_checksums.argtypes = [ctypes.c_void_p,
        ctypes.c_ubyte]
_ldb.leveldb_readoptions_set_fill_cache.argtypes = [ctypes.c_void_p,
        ctypes.c_ubyte]

_ldb.leveldb_create_iterator.argtypes = [ctypes.c_void_p,  ctypes.c_void_p]
_ldb.leveldb_create_iterator.restype = ctypes.c_void_p
_ldb.leveldb_iter_destroy.argtypes = [ctypes.c_void_p]
_ldb.leveldb_iter_valid.argtypes = [ctypes.c_void_p]
_ldb.leveldb_iter_valid.restype = ctypes.c_bool
_ldb.leveldb_iter_key.argtypes = [ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t)]
_ldb.leveldb_iter_key.restype = ctypes.c_void_p
_ldb.leveldb_iter_value.argtypes = [ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t)]
_ldb.leveldb_iter_value.restype = ctypes.c_void_p
_ldb.leveldb_iter_next.argtypes = [ctypes.c_void_p]
_ldb.leveldb_iter_prev.argtypes = [ctypes.c_void_p]
_ldb.leveldb_iter_seek_to_first.argtypes = [ctypes.c_void_p]
_ldb.leveldb_iter_seek_to_last.argtypes = [ctypes.c_void_p]
_ldb.leveldb_iter_seek.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_size_t]
_ldb.leveldb_iter_get_error.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_ldb.leveldb_writebatch_create.argtypes = []
_ldb.leveldb_writebatch_create.restype = ctypes.c_void_p
_ldb.leveldb_writebatch_destroy.argtypes = [ctypes.c_void_p]
_ldb.leveldb_writebatch_clear.argtypes = [ctypes.c_void_p]

_ldb.leveldb_writebatch_put.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
_ldb.leveldb_writebatch_delete.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_size_t]

_libc.free.argtypes = [ctypes.c_void_p]
_libc.memcpy.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]


Row = namedtuple('Row', 'key value')


class Error(Exception):
    pass


def _checkError(error):
    if bool(error):
        message = ctypes.string_at(error)
        _libc.free(ctypes.cast(error, ctypes.c_void_p))
        raise Error(message)


class Iter(object):
    """A wrapper around leveldb iterators. Can work like an idiomatic Python
    iterator, or can give you more control.
    """

    def __init__(self, db, verify_checksums=False, fill_cache=True,
            prefix=None):
        # DO NOT save a pointer to db in this iterator, as it will cause a
        # reference cycle
        assert not db._closed
        db._registerIterator(self)
        options = _ldb.leveldb_readoptions_create()
        _ldb.leveldb_readoptions_set_verify_checksums(options,
                verify_checksums)
        _ldb.leveldb_readoptions_set_fill_cache(options, fill_cache)
        self._iterator = _ldb.leveldb_create_iterator(db._db, options)
        _ldb.leveldb_readoptions_destroy(options)
        self._prefix = prefix

    def _close(self):
        if self._iterator:
            _ldb.leveldb_iter_destroy(self._iterator)
            self._iterator = None

    def __del__(self):
        self._close()

    def valid(self):
        """Returns whether the iterator is valid or not

        @rtype: bool
        """
        assert self._iterator
        valid = _ldb.leveldb_iter_valid(self._iterator)
        if self._prefix is None or not valid:
            return valid
        length = ctypes.c_size_t(0)
        val_p = _ldb.leveldb_iter_key(self._iterator, ctypes.byref(length))
        assert bool(val_p)
        return (ctypes.string_at(val_p, min(length.value, len(self._prefix)))
                == self._prefix)

    def seekFirst(self):
        """
        Jump to first key in database

        @return: self
        @rtype: Iter
        """
        assert self._iterator
        if self._prefix is not None:
            _ldb.leveldb_iter_seek(self._iterator, self._prefix,
                    len(self._prefix))
        else:
            _ldb.leveldb_iter_seek_to_first(self._iterator)
        self._checkError()
        return self

    def seekLast(self):
        """
        Jump to last key in database

        @return: self
        @rtype: Iter
        """
        assert self._iterator

        # if we have no prefix or the last possible prefix of this length, just
        # seek to the last key in the db.
        if self._prefix is None or self._prefix == "\xff" * len(self._prefix):
            _ldb.leveldb_iter_seek_to_last(self._iterator)
            self._checkError()
            return self

        # we have a prefix. see if there's anything after our prefix.
        # there's probably a much better way to calculate the next prefix.
        next_prefix = hex(long(self._prefix.encode('hex'), 16) + 1
                )[2:].rstrip("L")
        if len(next_prefix) % 2 != 0:
            next_prefix = "0" + next_prefix
        next_prefix = next_prefix.decode("hex")
        _ldb.leveldb_iter_seek(self._iterator, next_prefix, len(next_prefix))
        self._checkError()
        if _ldb.leveldb_iter_valid(self._iterator):
            # there is something after our prefix. we're on it, so step back
            _ldb.leveldb_iter_prev(self._iterator)
        else:
            # there is nothing after our prefix, just seek to the last key
            _ldb.leveldb_iter_seek_to_last(self._iterator)
        self._checkError()
        return self

    def seek(self, key):
        """Move the iterator to key. This may be called after StopIteration,
        allowing you to reuse an iterator safely.

        @param key: Where to position the iterator.
        @type key: str

        @return: self
        @rtype: Iter
        """
        assert self._iterator
        if self._prefix is not None:
            key = self._prefix + key
        _ldb.leveldb_iter_seek(self._iterator, key, len(key))
        self._checkError()
        return self

    def key(self):
        """Returns the iterator's current key. You should be sure the iterator
        is currently valid first by calling valid()

        @rtype: string
        """
        assert self._iterator
        length = ctypes.c_size_t(0)
        val_p = _ldb.leveldb_iter_key(self._iterator, ctypes.byref(length))
        assert bool(val_p)
        key = ctypes.string_at(val_p, length.value)
        if self._prefix is not None:
            return key[len(self._prefix):]
        return key

    def value(self):
        """Returns the iterator's current value. You should be sure the
        iterator is currently valid first by calling valid()

        @rtype: string
        """
        assert self._iterator
        length = ctypes.c_size_t(0)
        val_p = _ldb.leveldb_iter_value(self._iterator, ctypes.byref(length))
        assert bool(val_p)
        return ctypes.string_at(val_p, length.value)

    def __iter__(self):
        return self

    def next(self):
        """Advances the iterator one step. Also returns the current value prior
        to moving the iterator

        @rtype: Row (namedtuple of key, value)

        @raise StopIteration: if called on an iterator that is not valid
        """
        if not self.valid():
            raise StopIteration()
        rv = Row(self.key(), self.value())
        self.stepForward()
        return rv

    def prev(self):
        """Backs the iterator up one step. Also returns the current value prior
        to moving the iterator.

        @rtype: Row (namedtuple of key, value)

        @raise StopIteration: if called on an iterator that is not valid
        """
        if not self.valid():
            raise StopIteration()
        rv = Row(self.key(), self.value())
        self.stepBackward()
        return rv

    def stepForward(self):
        """Same as next but does not return any data or check for validity"""
        assert self._iterator
        _ldb.leveldb_iter_next(self._iterator)
        self._checkError()

    def stepBackward(self):
        """Same as prev but does not return any data or check for validity"""
        assert self._iterator
        _ldb.leveldb_iter_prev(self._iterator)
        self._checkError()

    def range(self, start_key=None, end_key=None, start_inclusive=True,
            end_inclusive=False):
        """A generator for some range of rows"""
        if start_key is not None:
            self.seek(start_key)
            if not start_inclusive and self.key() == start_key:
                self.stepForward()
        else:
            self.seekFirst()
        for row in self:
            if end_key is not None and (row.key > end_key or (
                    not end_inclusive and row.key == end_key)):
                break
            yield row

    def _checkError(self):
        error = ctypes.POINTER(ctypes.c_char)()
        _ldb.leveldb_iter_get_error(self._iterator, ctypes.byref(error))
        _checkError(error)


class WriteBatch(object):

    def __init__(self):
        self._puts = {}
        self._deletes = set()

    def put(self, key, val):
        self._deletes.discard(key)
        self._puts[key] = val

    def delete(self, key):
        self._puts.pop(key, None)
        self._deletes.add(key)

    def clear(self):
        self._puts = {}
        self.deletes = set()


class DBInterface(object):

    def close(self):
        raise NotImplementedError()

    def put(self, key, val, sync=False):
        raise NotImplementedError()

    def delete(self, key, sync=False):
        raise NotImplementedError()

    def get(self, key, verify_checksums=False, fill_cache=True):
        raise NotImplementedError()

    def write(self, batch, sync=False):
        raise NotImplementedError()

    def iterator(self, verify_checksums=False, fill_cache=True, prefix=None):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()

    def scope(self, prefix):
        raise NotImplementedError()

    def range(self, start_key=None, end_key=None, start_inclusive=True,
            end_inclusive=False, verify_checksums=False, fill_cache=True):
        return self.iterator(verify_checksums=verify_checksums,
                fill_cache=fill_cache).range(start_key=start_key,
                        end_key=end_key, start_inclusive=start_inclusive,
                        end_inclusive=end_inclusive)


class DB(DBInterface):

    def __init__(self, path, bloom_filter_size=10, create_if_missing=False,
            error_if_exists=False, paranoid_checks=False,
            write_buffer_size=(4*1024*1024), max_open_files=1000,
            block_cache_size=(8*1024*1024), block_size=(4*1024)):
        DBInterface.__init__(self)
        self._filter_policy = _ldb.leveldb_filterpolicy_create_bloom(
                bloom_filter_size)
        self._cache = _ldb.leveldb_cache_create_lru(block_cache_size)
        self._db = None
        self._closed = False
        self._iterators = weakref.WeakValueDictionary()
        options = _ldb.leveldb_options_create()
        _ldb.leveldb_options_set_filter_policy(options, self._filter_policy)
        _ldb.leveldb_options_set_create_if_missing(options, create_if_missing)
        _ldb.leveldb_options_set_error_if_exists(options, error_if_exists)
        _ldb.leveldb_options_set_paranoid_checks(options, paranoid_checks)
        _ldb.leveldb_options_set_write_buffer_size(options, write_buffer_size)
        _ldb.leveldb_options_set_max_open_files(options, max_open_files)
        _ldb.leveldb_options_set_cache(options, self._cache)
        _ldb.leveldb_options_set_block_size(options, block_size)
        error = ctypes.POINTER(ctypes.c_char)()
        db = _ldb.leveldb_open(options, path, ctypes.byref(error))
        _ldb.leveldb_options_destroy(options)
        _checkError(error)
        self._db = db

    def close(self):
        closed, self._closed = self._closed, True
        if not closed:
            for iterator in self._iterators.valuerefs():
                iterator = iterator()
                if iterator is not None:
                    iterator._close()
            self._iterators = weakref.WeakValueDictionary()
            if self._db:
                _ldb.leveldb_close(self._db)
            _ldb.leveldb_cache_destroy(self._cache)
            _ldb.leveldb_filterpolicy_destroy(self._filter_policy)

    def __del__(self):
        self.close()

    def _registerIterator(self, iterator):
        self._iterators[id(iterator)] = iterator

    def put(self, key, val, sync=False):
        error = ctypes.POINTER(ctypes.c_char)()
        options = _ldb.leveldb_writeoptions_create()
        _ldb.leveldb_writeoptions_set_sync(options, sync)
        _ldb.leveldb_put(self._db, options, key, len(key), val, len(val),
                ctypes.byref(error))
        _ldb.leveldb_writeoptions_destroy(options)
        _checkError(error)

    def delete(self, key, sync=False):
        error = ctypes.POINTER(ctypes.c_char)()
        options = _ldb.leveldb_writeoptions_create()
        _ldb.leveldb_writeoptions_set_sync(options, sync)
        _ldb.leveldb_delete(self._db, options, key, len(key),
                ctypes.byref(error))
        _ldb.leveldb_writeoptions_destroy(options)
        _checkError(error)

    def get(self, key, verify_checksums=False, fill_cache=True):
        error = ctypes.POINTER(ctypes.c_char)()
        options = _ldb.leveldb_readoptions_create()
        _ldb.leveldb_readoptions_set_verify_checksums(options,
                verify_checksums)
        _ldb.leveldb_readoptions_set_fill_cache(options, fill_cache)
        size = ctypes.c_size_t(0)
        val_p = _ldb.leveldb_get(self._db, options, key, len(key),
                ctypes.byref(size), ctypes.byref(error))
        if bool(val_p):
            val = ctypes.string_at(val_p, size.value)
            _libc.free(ctypes.cast(val_p, ctypes.c_void_p))
        else:
            val = None
        _ldb.leveldb_readoptions_destroy(options)
        _checkError(error)
        return val

    def write(self, batch, sync=False):
        real_batch = _ldb.leveldb_writebatch_create()
        for key, val in batch._puts.iteritems():
            _ldb.leveldb_writebatch_put(real_batch, key, len(key), val,
                    len(val))
        for key in batch._deletes:
            _ldb.leveldb_writebatch_delete(real_batch, key, len(key))
        error = ctypes.POINTER(ctypes.c_char)()
        options = _ldb.leveldb_writeoptions_create()
        _ldb.leveldb_writeoptions_set_sync(options, sync)
        _ldb.leveldb_write(self._db, options, real_batch,
                ctypes.byref(error))
        _ldb.leveldb_writeoptions_destroy(options)
        _ldb.leveldb_writebatch_destroy(real_batch)
        _checkError(error)

    def iterator(self, verify_checksums=False, fill_cache=True, prefix=None):
        return Iter(self, verify_checksums=verify_checksums,
                fill_cache=fill_cache, prefix=prefix)

    def __iter__(self):
        return Iter(self).seekFirst()

    def scope(self, prefix, allow_close=False):
        return ScopedDB(self, prefix, allow_close=allow_close)


class ScopedDB(DBInterface):

    def __init__(self, db, prefix, allow_close=False):
        self._db = db
        self._prefix = prefix
        self._allow_close = allow_close

    def close(self):
        if self.allow_close:
            self._db.close()

    def put(self, key, *args, **kwargs):
        self._db.put(self._prefix + key, *args, **kwargs)

    def delete(self, key, *args, **kwargs):
        self._db.delete(self._prefix + key, *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return self._db.get(self._prefix + key, *args, **kwargs)

    def write(self, batch, *args, **kwargs):
        unscoped_batch = WriteBatch()
        for key, value in batch._puts.iteritems():
            unscoped_batch._puts[self._prefix + key] = value
        for key in batch._deletes:
            unscoped_batch._deletes.add(self._prefix + key)
        self._db.write(unscoped_batch, *args, **kwargs)

    def iterator(self, verify_checksums=False, fill_cache=True, prefix=None):
        if prefix is None:
            prefix = self._prefix
        else:
            prefix = self._prefix + prefix
        return Iter(self._db, verify_checksums=verify_checksums,
                fill_cache=fill_cache, prefix=prefix)

    def __iter__(self):
        return Iter(self._db, prefix=self._prefix).seekFirst()

    def scope(self, prefix):
        return self._db.scope(self._prefix + prefix)

