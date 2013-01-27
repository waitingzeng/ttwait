#!/usr/bin/python
#coding=utf8
import sys


def cal_checksum_bit(barcode):
    weight = (1, 3)
    assert len(barcode) == 12

    s = sum(weight[i % 2] * int(x) for i, x in enumerate(barcode))
    return str((10 - s % 10) % 10)


def get_barcode(barcode):
    return barcode + cal_checksum_bit(barcode)


if __name__ == '__main__':
    print get_barcode(sys.argv[1])
