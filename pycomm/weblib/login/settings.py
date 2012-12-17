#! /usr/bin/env python
#coding=utf-8
import os.path as osp
import sys

CUR_PATH = osp.dirname(osp.abspath(__file__))

APPNAME = osp.basename(CUR_PATH)
from web.settings import get_app_settings

settings = get_app_settings(APPNAME)
render = settings.render
