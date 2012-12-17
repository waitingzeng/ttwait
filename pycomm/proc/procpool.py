#!/usr/bin/evn python

import os
import sys
import signal
from pycomm.log import log
from .basic import ProcBase, WorkerFinishException


class ProcPool( ProcBase ):
    def _init(self):
        self.worker_id_map = {}
        signal.signal( signal.SIGTERM, self.terminate )

    def get_worker_name(self, id):
        return 'worker[%s:%s]' % (id, os.getpid())

    def __del__( self ):
        self.kill_children()

    def kill_children( self ):
        if hasattr(self, 'conf_file') and self.conf_file:
            self.running = False

            for pid in self.worker_id_map.keys():
                print 'killing %d' % pid
                try:
                    os.kill( pid, signal.SIGTERM )
                except:
                    pass
            self.worker_id_map = {}


    def update_pids_file( self ):
        pidsfile = open( self.pidsfile, 'w' )
        pids = '\n'.join(str(x) for x in self.worker_id_map.keys())
        pidsfile.write( '%s\n' % os.getpid() )   
        pidsfile.write( '%s\n' % pids )
        pidsfile.close()

    def append_pids_file( self ):
        pidsfile = open( self.pidsfile, 'a' )
        pidsfile.write( '%s\n' % os.getpid() )   
        pidsfile.close()

    def terminate( self, signum, frame ):
        if signum == signal.SIGTERM:
            self.kill_children()
    
    def main_loop(self):
        while self.running:
            pid, status = os.wait()

            print 'process exit somehow, pid %d, status %x' % ( pid, status )
            log.trace( 'process exit somehow, pid %d, status %x' % ( pid, status ) )
            if pid:
                self.some_worker_exit( pid, status )
                id = self.worker_id_map.pop( pid )
                if status != 1000:
                    pid = self.create_worker( id )
                    if pid is None:
                        log.error( 'create_worder failed! %s', id )
    

    def worker_terminate( self, signum, frame ):
        print 'worker %d is terminating' % os.getpid()
        self.running = False
        sys.exit()
    

    def some_worker_exit(self, pid, status=0):
        pass

    def begin_run_worker(self, name, id):
        signal.signal( signal.SIGTERM, self.worker_terminate )


    def create_worker( self, id ):
        try:
            pid = os.fork()
        except OSError as (errno, strerror):
            log.error( "OSError: ({0}): {1}, {2}".format(errno, strerror, id) )
            return None

        #child
        if 0 == pid:
            try:
                self.worker(id)
            except WorkerFinishException:
                sys.exit(1000)
            except:
                log.exception("worker exception")
                sys.exit(-1)
            sys.exit(0) 
        #parent
        elif pid > 0:
            self.worker_id_map[ pid ] = id
            self.update_pids_file( )
            return pid
        else:
            print 'Error while forking'
            return None

