#! /usr/bin/env python
#coding=utf-8

def template_hook():
    webpy.template.Template.globals['static'] = webpy.ctx.session

def create_hook(app):
    if webpy.config.get('_session') is None: 
        session = webpy.session.Session(None, webpy.session.DiskStore('/home/qspace/data/sessions/'), 
            initializer={
                'uin' : 0,
                'is_debug' : False,
               }
           )
        webpy.config._session = session
    
    app.add_processor(webpy.config._session._processor)
    app.add_processor(webpy.loadhook(session_hook))
    