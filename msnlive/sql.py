#! /usr/bin/env python
#coding=utf-8
import sys

def main():
    filename = sys.argv[1]
    fsql = file('sql.txt', 'w')
    for line in file(filename):
        line = line.strip()
        sql = "insert ignore user (name) values ('%s');\n" % line
        fsql.write(sql)
        sql = "update user set hadadd=1 where name='%s';\n" % line
        fsql.write(sql)
    fsql.close()
    
if __name__ == '__main__':
    main()