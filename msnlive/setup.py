#! /usr/bin/env python
#coding=utf-8
from distutils.core import setup
import py2exe
setup(console = [{"script": "run.py", },{"script": "export.py", },{"script": "search.py", },{"script": "search_google.py", },{"script": "addFriend.py", },{"script": "delFriend.py", },])
