import os
import sys
import time
import traceback
import string
import types
from datetime import datetime
from functools import partial


_PATH_PREFIX = os.environ.get('LOGPATH', "/home/webuser/logs")
_LOG_FILEFORMAT = os.environ.get('LOGFILEFORMAT', '%Y%m%d%H')
import logging
try:
    import codecs
except ImportError:
    codecs = None

FORMAT = "<%(levelname)s> <%(name)s:%(filename)s:%(lineno)d:%(funcName)s> <%(process)d:%(threadName)s>%(asctime)-8s] %(message)s"
#FORMAT = "<%(levelname)s> <%(name)s> <%(process)d:%(threadName)s>%(asctime)-8s] %(message)s"



#---------------------------------------------------------------------------
#   Miscellaneous module data
#---------------------------------------------------------------------------

#
# _srcfile is used when walking the stack to check when we've got the first
# caller stack frame.
#
if hasattr(sys, 'frozen'): #support for py2exe
    _srcfile = "logging%s__init__%s" % (os.sep, __file__[-4:])
elif string.lower(__file__[-4:]) in ['.pyc', '.pyo']:
    _srcfile = __file__[:-4] + '.py'
else:
    _srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

# next bit filched from 1.5.2's inspect.py
def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_traceback.tb_frame.f_back

if hasattr(sys, '_getframe'): currentframe = lambda: sys._getframe(3)



TRACE = 1000
logging.addLevelName(TRACE, 'TRACE')

getLogger = logging.getLogger

def open_log(name=None, log_level=logging.DEBUG, path=None, format=FORMAT):

    log = getLogger(name)
    if log.handlers:
        for h in log.handlers:
            if h.__class__ == ErrorFileHandler:
                return

    fmt = logging.Formatter(format, '%Y-%m-%d_%H:%M:%S')

    if path is None:
        path = _PATH_PREFIX
    handler = ErrorFileHandler(path)
    handler.setFormatter(fmt)    

    log.addHandler(handler)
    
    if not log_level:
        log_level = logging.DEBUG
    
    log.setLevel(log_level)

    logging.root = log

    globals()['cur_log'] = log

    return log


def open_debug():
    if cur_log.handlers:
        for h in cur_log.handlers:
            if h.__class__ == logging.StreamHandler:
                return

    handler = logging.StreamHandler()
    handler.setFormatter(cur_log.handlers[-1].formatter)
    cur_log.addHandler(handler)    
    return cur_log

class StdOut(object):
    def __getattr__(self, name):
        return functools.partial(self.proxy_func, name=name)

    def proxy_func(self, *args, **kwags):
        name = kwargs.pop('name', None)
        if not name:
            return 
        try:
            return getattr(sys.stdout, name)(*args, **kwargs)
        except:
            return

class ErrorFileHandler(logging.StreamHandler):
    """
    A handler class which writes formatted logging records to disk files.
    """
    __base__ = logging.StreamHandler
    max_bytes = 3000 * 1024 * 1024
    def __init__(self, path, encoding=None, delay=0):
        if codecs is None:
            encoding = None
        self.path = path
        self.encoding = encoding
        if delay:
            logging.Handler.__init__(self)
            self.stream = None
        else:
            self.__base__.__init__(self, self._open())
        self.fatal_fmt = None

    def get_cur_filename(self):
        t = datetime.now()
        newlogfile = "%s/%s.log" % (self.path, t.strftime(_LOG_FILEFORMAT))
        return newlogfile
    

    def close(self):
        """
        Closes the stream.
        """
        if self.stream:
            self.flush()
            if hasattr(self.stream, "close"):
                self.stream.close()
            self.__base__.close(self)
            self.stream = None

    def _open(self):
        try:
            if self.encoding is None:
                stream = open(self.get_cur_filename(), 'a')
            else:
                stream = codecs.open(self.get_cur_filename(), 'a', self.encoding)
            try:
                os.popen('chmod 777 %s' % self.get_cur_filename())
            except:
                pass
            return stream
        except IOError:
            return StdOut()

    def _get_stream(self):
        if self.stream is None:
            self.stream = self._open()
        else:
            cur_filename = self.get_cur_filename()
            if cur_filename != self.stream.name:
                self.stream = self._open()
            
            if self.max_bytes > 0:
                self.stream.seek(0, 2)
                if self.stream.tell() >= self.max_bytes:
                    raise Exception(str(self.stream.tell()))
        return self.stream

    def emit(self, record):
        """
        Emit a record.

        If the stream was not opened because 'delay' was specified in the
        constructor, open it before calling the superclass's emit.
        """
        try:
            stream = self._get_stream()
        except:
            #traceback.print_exc()
            return
        return self.__base__.emit(self, record)




class LogProxy(object):

    def __getattr__(self, name):
        return getattr(cur_log, name)

    def trace(self, msg, *args):
        return self._log(TRACE, msg, args)
    
    def exception(self, msg='', *args, **kwargs):
        exc_info = kwargs.pop('exc_info', None)
        if args:
            info = msg % args
        else:
            info = msg
        
        if exc_info:
            trace_info = sys.exc_info()
        else:
            trace_info = traceback.format_exc().split('\n')
        if not trace_info:
            cur_log.error(info)
        else:
            for _info in trace_info:
                if not _info:
                    continue
                self._log(logging.ERROR, info + ' ' + _info, (),)

    def debug(self, msg, *args, **kwargs):
        if cur_log.isEnabledFor(logging.DEBUG):
            self._log(logging.DEBUG, msg, args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if cur_log.isEnabledFor(logging.INFO):
            self._log(logging.INFO, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if cur_log.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, msg, args, **kwargs)

    warn = warning

    def error(self, msg, *args, **kwargs):
        if cur_log.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, msg, args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        if self.isEnabledFor(CRITICAL):
            self._log(CRITICAL, msg, args, **kwargs)

    fatal = critical

    def log(self, level, msg, *args, **kwargs):
        if type(level) != types.IntType:
            if raiseExceptions:
                raise TypeError, "level must be an integer"
            else:
                return
        if cur_log.isEnabledFor(level):
            self._log(level, msg, args, **kwargs)

    def find_caller(self):
        f = currentframe()
        #On some versions of IronPython, currentframe() returns None if
        #IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == _srcfile:
                f = f.f_back
                continue
            rv = (filename, f.f_lineno, co.co_name)
            break
        return rv

    def _log(self, level, msg, args, exc_info=None, extra=None):
        if _srcfile:
            #IronPython doesn't track Python frames, so findCaller throws an
            #exception. We trap it here so that IronPython can use logging.
            try:
                fn, lno, func = self.find_caller()
            except ValueError:
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if type(exc_info) != types.TupleType:
                exc_info = sys.exc_info()
        try:
            record = cur_log.makeRecord(cur_log.name, level, fn, lno, msg, args, exc_info, func, extra)
            cur_log.handle(record)
        except:
            print 'log info fail ', level, msg, args, exc_info, extra
            


class StdErr(object):
    def write(self, *args, **kwargs):
        return log.exception(*args, **kwargs)

stderr = StdErr()

class StdOut(object):
    def write(self, *args, **kwargs):
        return log.info(*args, **kwargs)
stdout = StdOut()

class PrefixLog(object):
    def __init__(self, prefix, *args):
        self.prefix = prefix
        if args:
            self.prefix = self.prefix % args
        
    def _func(self, name, info='', *args, **kwargs):
        return getattr(log, name)('%s %s' % (self.prefix, info), *args)
        
    def __getattr__(self, name):
        return partial(self._func, name)
    
    def __call__(self, *args, **kwargs):
        self.trace(*args, **kwargs)

    
class WSGILogApplication(object):
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, *args, **kwargs):
        environ['wsgi.errors'] = stderr
        try:
            return self.application(environ, *args, **kwargs)
        except:
            log.exception()
            raise

other_log = open_log('OTHER')
cur_log = other_log

log = LogProxy()

logging.getLogger = lambda x=None:log

logging.root =  log
logging.Logger.root = log



if __name__ == '__main__':
    open_log('aaa', path='C:\\')
    open_debug()
    mylog = PrefixLog('bbb')
    def b():
        return s
    def a():
        try:
            b()
        except:
            mylog.exception("test error")
        
    a()
