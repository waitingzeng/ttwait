#!/usr/bin/python
#coding=utf8
from pycomm.utils.storage import Const

class OrderStatus(Const):
    unpaid = (0, 'Unpaid')
    paid = (1, 'Paid')
    delivery = (2, 'Delivery')
