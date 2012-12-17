#! /usr/bin/env python
#coding=utf-8
from datetime import datetime

def timesince_cn(timestamp):
    date = datetime.fromtimestamp(float(timestamp))

    delta = datetime.now() - date

    num_years = delta.days / 365
    if (num_years > 0):
        return u"%d 年之前" % num_years

    num_weeks = delta.days / 7
    if (num_weeks > 0):
        return u"%d 星期之前" % num_weeks

    if (delta.days > 0):
        num_hours = delta.seconds / 3600
        if (num_hours > 0):
            return u"%d 天 %d 小时之前" % (delta.days, num_hours)
        return u"%d 天之前" % delta.days

    num_hours = delta.seconds / 3600
    if (num_hours > 0):
        return u"%d 小时之前" % num_hours

    num_minutes = delta.seconds / 60
    if (num_minutes > 0):
        return u"%d 分钟之前" % num_minutes

    return u"%d 秒之前" % delta.seconds
