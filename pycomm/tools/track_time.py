#! /usr/bin/env python
#coding=utf-8
from pycomm.log import log
import time
import sys
from cStringIO import StringIO
import re

MAX_NODE = 32
class Node(object):
    def __init__(self, name):
        self.name = name
        self.count = 0
        self.ntime = 0
        self.total_node = 0
        self.childs = []
        
valid_name_re = re.compile('[^A-Za-z0-9\:_\.]')
class T(object):
    main_node = None
    cur_node = None
    oss_track = False
    application = ''
    def __init__(self, name=None):
        self.tv_start = time.time()
        self.last_node = T.cur_node
        self.node = None
        if name is None:
            name = sys._getframe(1).f_code.co_name
        else:
            name = name.replace(' ', '_')
        self.node = self.get_node(name)
        if self.node:
            T.cur_node = self.node

    def get_node(self, name):
        name = valid_name_re.sub('_', name)
        # 主节点为空, 初始化主节点
        if T.cur_node is None:
            T.main_node = Node(name)
            T.cur_node = T.main_node
            return T.cur_node

	    # 先确认本节点是否存在同样的标示
        for node in T.cur_node.childs:
            if node.name == name:
                return node
	    
        if len(T.cur_node.childs) > MAX_NODE:
            log.error("TRACK: Node[%s] reach the MAX.", T.cur_node.name)
            return None

        # 创建新的标示
        node = Node(name)
        T.cur_node.childs.append(node)

        # 切换
        return node


    def __del__(self):
        self.stop()

    
    def get_time(self):
        # 得到执行时间
        tv_end = time.time()

        diff = int(1000 * (tv_end - self.tv_start))
        return diff

    def stop(self):
        if not self.node:
            return

        # 记录本节点信息
        self.node.count += 1
        self.node.ntime += self.get_time()
        

        # 恢复到上一节点
        T.cur_node = self.last_node
        self.node = None

        #if T.cur_node is None:
        #    T.track()
    
    @classmethod
    def clear(cls):
        cls.main_node = None
        cls.cur_node = None

    @classmethod
    def track(cls):
        if cls.cur_node:
            log.error("TRACK: Main Object not release or other %s", cls.cur_node.name)
            return
        if not cls.main_node:
            return 
        buf = StringIO()
        buf.write('1 TRACK: track_time(,) ')
        cls.traveral_node(cls.main_node, cls.main_node.name, buf)
        
    	cls.clear()
        return log.trace(buf.getvalue())
    
    @classmethod
    def traveral_node(cls, node, name, buf):
        if not node:
            return
        if node != cls.main_node:
            name = '%s::%s' % (name, node.name)

        if node.count == 0:
            log.error("TRACK: object(%s) not release", name)
            del node
            return
        
        tmp = " Cnt=%d Time=%d " % (node.count, node.ntime)
        
        #if T.oss_track:
            #OssLogInfo(OSS_PREID_WEBMAIL_CGIFUN_TIME, "%s,%s,%d,%d", T.application, name, node->ntime, node->count)

        buf.write(name)
        buf.write(tmp)
        for child in node.childs:
            cls.traveral_node(child, name, buf)
        
        del node
        
TrackTime = T

__all__ = ['TrackTime']

if __name__ == '__main__':
    from pycomm.log import open_log
    
    open_log('track')
    def a():
        t = T('ina')
        time.sleep(1)
        
    
    t = T('begin')
    a()
    time.sleep(0.001)
    t.stop()
    print T.track()
