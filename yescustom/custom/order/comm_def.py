#!/usr/bin/python
#coding=utf8
from pycomm.utils.storage import Const

class OrderStatus(Const):
    unpaid = (0, '末支付')
    paid = (1, '已支付')
    delivery = (2, '已派送')
