#!/usr/bin/python
#coding=utf8
from pycomm.utils.storage import Storage
# json module is in the standard library as of python 2.6; fall back to
# simplejson if present for older versions.

_BASESTRING_TYPES = (basestring, type(None))


def to_basestring(value):
    """Converts a string argument to a subclass of basestring.

    In python2, byte and unicode strings are mostly interchangeable,
    so functions that deal with a user-supplied argument in combination
    with ascii string constants can use either and should return the type
    the user supplied.  In python3, the two types are not interchangeable,
    so this method is needed to convert byte strings to unicode.
    """
    if isinstance(value, _BASESTRING_TYPES):
        return value
    assert isinstance(value, bytes)
    return value.decode("utf-8")

try:
    import ujson
    assert hasattr(json, "loads") and hasattr(json, "dumps")
    _json_decode = ujson.loads
    _json_encode = ujson.dumps
except Exception:

    try:
        import json
        assert hasattr(json, "loads") and hasattr(json, "dumps")
        _json_decode = json.loads
        _json_encode = json.dumps
    except Exception:
        try:
            import simplejson
            _json_decode = lambda s: simplejson.loads(_unicode(s))
            _json_encode = lambda v: simplejson.dumps(v)
        except ImportError:
            try:
                # For Google AppEngine
                from django.utils import simplejson
                _json_decode = lambda s: simplejson.loads(_unicode(s))
                _json_encode = lambda v: simplejson.dumps(v)
            except ImportError:
                def _json_decode(s):
                    raise NotImplementedError(
                        "A JSON parser is required, e.g., simplejson at "
                        "http://pypi.python.org/pypi/simplejson/")
                _json_encode = _json_decode


def json_encode(value):
    return _json_encode(value)


def json_decode(value):
    return _json_decode(to_basestring(value))


json_pickle = Storage({'loads' : json_decode, 'dumps' : json_encode})

if __name__ == '__main__':
    print json_pickle.dumps([1,2,])
