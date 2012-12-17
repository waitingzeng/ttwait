#!/usr/bin/python
#coding=utf8
import xlrd
from datetime import datetime



def load_excel(filename=None, file_contents=None,  sheet_index=0):
    bk = xlrd.open_workbook(filename=filename, file_contents=file_contents)
    try:
        sh = bk.sheet_by_index(sheet_index)
    except:
        return None

    
    nrows = sh.nrows
    ncols = sh.ncols
     
    row_list = []
    for i in range(0,nrows):
        #row_data = sh.row_values(i)
        row_data = []
        for j in range(0, ncols):
            value = sh.cell_value(i, j)
            t = sh.cell_type(i, j)
            if t == xlrd.XL_CELL_DATE:
                value = xlrd.xldate_as_tuple(value, 0)
                value = datetime(*value)
            row_data.append(value)
        row_list.append(row_data)

    return row_list

