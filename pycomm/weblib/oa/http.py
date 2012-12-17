#! /usr/bin/env python2.6
#coding=utf-8

from py3rd import webpy
def get_referer():
    return webpy.ctx.env.get('HTTP_REFERER','')
def get_host():
    return webpy.ctx.env.get('HTTP_HOST','')
def get_uri():
    return webpy.ctx.env.get('REQUEST_URI','')

