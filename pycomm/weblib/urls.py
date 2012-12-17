#! /usr/bin/env python
#coding=utf-8
import views

urls = [
    '/auto_ck', views.auto_ck,
    '/env', views.env,
    '/.*', views.auto_slash,
]