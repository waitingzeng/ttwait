#!/usr/bin/python
#coding=utf8
import os


def get_info(path='/'):
    disk = os.statvfs(path)
    
    total_bytes = float(disk.f_bsize*disk.f_blocks)
    total_used_space = float(disk.f_bsize*(disk.f_blocks-disk.f_bfree))
    total_avai_space = float(disk.f_bsize*disk.f_bfree)
    total_avail_space_non_root = float(disk.f_bsize*disk.f_bavail)
    return total_bytes, total_used_space, total_avai_space, total_avail_space_non_root

def get_used_ratio(path='/'):
    info = get_info(path)
    return info[1] / info[0]


if __name__ == '__main__':
    print get_used_ratio()
