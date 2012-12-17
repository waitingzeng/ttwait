#! /usr/bin/env python
#coding=utf-8
from py3rd import webpy
import marshal as pickle
import os
from pycomm.tools.track_time import TrackTime

class Session(webpy.session.Session):
    def _save(self):
        T = TrackTime('session_save')
        super(self.__class__, self)._save()
        T.stop()

class DiskStore(webpy.session.DiskStore):
    def __getitem__(self, key):
        path = self._get_path(key)
        if os.path.exists(path): 
            pickled = open(path, 'rb').read()
            return self.decode(pickled)
        else:
            raise KeyError, key

    def __setitem__(self, key, value):
        path = self._get_path(key)
        pickled = self.encode(value)
        if not pickled:
            return
        try:
            f = open(path, 'wb')
            try:
                f.write(pickled)
            finally: 
                f.close()
        except IOError:
            pass
    
    def cleanup(self, timeout):
        now = time.time()
        for f in os.listdir(self.root):
            path = self._get_path(f)
            atime = os.stat(path).st_atime
            if now - atime > timeout :
                os.remove(path)

    def encode(self, session_dict):
        """encodes session dict as a string"""
        try:
            return pickle.dumps(session_dict)
        except:
            return ''
        

    def decode(self, session_data):
        """decodes the data to get back the session dict """
        try:
            return pickle.loads(session_data)
        except:
            return {}
    

def session_hook():
    webpy.ctx.session = webpy.config.get('_session')
    webpy.template.Template.globals['session'] = webpy.ctx.session

def create_session():
    if webpy.config.get('_session') is None: 
        session = Session(None, DiskStore('/home/qspace/data/sessions/'), 
            initializer={
                'uin' : 0,
                'is_debug' : False,
               }
           )
        webpy.config._session = session
    

def create_hook(app):
    create_session()
    app.add_processor(webpy.config._session._processor)
    app.add_processor(webpy.loadhook(session_hook))
    
