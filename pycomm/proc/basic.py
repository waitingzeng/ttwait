#!/usr/bin/evn python
import os
import sys
import os.path as osp
import logging
from optparse import OptionParser

from pycomm.log import log,open_log, open_debug
from pycomm.utils import daemonize
from pycomm.utils.dict4ini import DictIni

class WorkerFinishException(Exception):
    pass

class ProcBase(object):
    def __init(self, config_file):
        
        self.debug = False
        if not osp.exists(config_file):
            raise Exception('%s does not exists', config_file)
        self.conf_file = config_file
        self.conf = DictIni(self.conf_file)
        self.appname = self.conf.appname or self.conf.name or ''
        self.worker_num = self.conf.workers or self.conf.thread_num or self.conf.proc_num or 1
        open_log(self.appname + (self.options.logname or ''), self.conf.loglevel or logging.INFO, self.conf.logpath or '/root/data/log', log_type=self.conf.logtype, max_bytes=self.conf.max_bytes or 0, backup_count=self.conf.backup_count or 0)

        
        self.pidfile = '/tmp/' + self.appname + '.pid'
        self.pidsfile = '/tmp/' + self.appname + '.pids'
        self.loop_number = self.conf.loop_number or 0
        
        self.total = 0
        self.running = True
        self._init()
        self.init()

    def _init(self):
        pass

    def init(self):
        pass

    def killall(self):
        for f in [self.pidfile, self.pidsfile]:
            if os.path.exists(f):
                for pid in file(f):
                    try:
                        pid = int(pid.strip())
                        os.popen('kill -9 %s' % pid).read()
                        print 'kill', pid
                    except:
                        continue

    
    def create_pid_file( self ):
        pidfile = open( self.pidfile, 'w' ) 
        pidfile.write( '%u\n' % os.getpid() )
        pidfile.close()

    def update_pids_file( self ):
        pass

    def unlink( self, filepath ):
        try:
            os.unlink( filepath );
        except:
            pass

    

    def _start( self ):
        self.before_start_worker()

        for i in range( 1, self.worker_num + 1 ):
            self.create_worker( i )

        self.after_start_worker()
        self.main_loop()
    
    def start(self):
        self.unlink( self.pidfile )
        self.unlink( self.pidsfile )
        if not self.debug and self.conf.daemon:
            print 'becoming daemon', os.getpid()
            daemonize.become_daemon()
        else:
            print 'no daemon', os.getpid()
            open_debug()

        self.create_pid_file()
        self._start()

    def work( self , name, id):
        raise NotImplementedError

    def before_start_worker(self):
        pass
    
    def after_start_worker(self):
        pass
    

    def begin_run_worker(self, name, id):
        """run in child"""
        pass

    def after_run_worker(self,name, id):
        """run in child"""
        pass
    
    def get_worker_name(self, id):
        return 'worker[%d]' % id
    
    def worker( self, id=0): 
        name = self.get_worker_name(id)
        log.debug('worker[%s] begin running' % ( name,) )

        self.begin_run_worker(name, id)
        count = 0
        while self.running:
            count += 1
            log.debug( '%s is doing his job for %d times...' % ( name, count ) )

            if self.loop_number > 0 and count > self.loop_number:
                log.debug( '%s loop %d times, exit' % ( name, self.loop_number) ); 
                break
            try:
                self.work(name, id)
            except WorkerFinishException:
                log.trace('%s finish' % name)
                break
            except:
                log.exception('%s had some error', name)
                raise

        self.after_run_worker(name, id)

    def create_worker( self, id ):
        raise NotImplementedError

    def test_init(self, options):
        pass

    def add_options(self, parser):
        pass

    def process_options(self, options, args):
        return False

    def run(self):
        self.parser = parser = OptionParser(conflict_handler='resolve')
        parser.add_option("-i", "--conf", dest="conf", action="store",
                  help="[MUST] the conf file to setup", type="string")
        parser.add_option("-r", '--restart', dest='restart', action="store_true", help="restart")
        parser.add_option("-s", '--stop', dest='stop', action="store_true", help="stop")
        parser.add_option('--test', dest='test', action="store_true", help="run test")
        parser.add_option("-d", '--debug', dest='debug', action="store_true", help="run debug, no daemon and open_debug")
        parser.add_option('--worker_num', dest='worker_num', action="store", help="the thread num", type='int')
        parser.add_option('--logname', dest='logname', action="store", help="the extra log name", type='string')
        parser.add_option('--logtype', dest='logtype', action="store", help="the loggint type", type='string')
        parser.add_option('--gevent', dest='gevent', action="store_true", help="run with gevent")
        parser.add_option('--maxrunning', dest='maxrunning', action="store", help="maxrunning", type='int')
        
        self.add_options(parser)

        self.options, self.args = options, args = parser.parse_args(sys.argv[1:])
        if not options.conf:
            parser.print_help()
            sys.exit(-1)
        
        if self.process_options(options, args):
            parser.print_help()
            sys.exit(-2)
            
        self.options = options
        self.__init( options.conf )
        if options.debug:
            self.debug = True
        if options.test:
            self.test_init(options)
            open_debug()
            self.worker(1)
            return
        if options.stop:
            self.killall()
            return
        if options.restart:
            self.killall()
        if options.worker_num:
            self.worker_num = options.worker_num
        if options.gevent:
            from gevent import monkey
            monkey.patch_all()
        self.start()
