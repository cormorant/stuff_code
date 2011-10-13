#!/usr/bin/env python
# coding: utf-8
"""
Программа для переименовании названия станции в файлах, записанных
аппаратурой Иркут. Добавляется ".st".
"""
#TODO: переписать на классы
#__version__="0.0.1"

import os, sys
import struct
#import tempfile; TMP = tempfile.gettempdir()
#import libBaikal

SUFFIX = ".st" # что прибавлять к имени станции

def is_baikal(fname):
    """ Является параметр файлом непрерывной записи """
    try:
        fil = open(fname, 'rb')
        fil.seek(18)
        razr = struct.unpack( 'h', fil.read(2) )[0]
        fil.close() # закроем файл
    except IOError:
        print "Error checking file "+fname
        sys.exit(1)
    # является ли числом
    try: razr = int(razr)
    except ValueError: return False
    # проверить разрядность. Должна быть 16 или 24
    if razr in (16, 24): return True
    else: return False

def stripnulls(s):
    """ очищает строку от символов пропуска и нулевых символов """
    return s.replace("\00", '').replace("\01", '').replace(SUFFIX, '').strip()

def rename(fname):
    """ Функции передаются название папки, или список файлов,
    и все они переименовываются """
    # открыть файл, считать название станции из заголовка
    try:
        fil = open(fname, 'rb')
        try:
            data = fil.read() # сохраним данные файла
            fil.seek(32)
            station = stripnulls( struct.unpack('16s', fil.read(16) )[0] )
        finally:
            fil.close() # закроем файл
    except IOError:
        print "Error reading file "+fname
        sys.exit(1)
    # добавить суффикс к названию
    station = station + SUFFIX
    # перезаписать результат в файл
    try:
        fil = open(fname, 'wb')
        try:
            fil.write(data)
            fil.seek(32)
            #struct.pack_into('16s', fil, 32, station)
            fil.write( struct.pack('16s', station) )
        finally:
            fil.close() # закроем файл
    except IOError:
        print "Error writing file "+fname
        sys.exit(1)
    
if __name__ == "__main__":
    # смотрим параметры, переданные программе, и работаем
    if len( sys.argv ) < 2:
        print "Please spicify full path to destination."
        print "Usage: python renamest.py <path_to_dir>"
        sys.exit(1)
    # Работаем с переданной папкой
    BasePath = sys.argv[1]
    # существует ли путь
    if not os.path.exists(BasePath):
        print "Path doesn't exists"
        sys.exit(1)
    print "Work with path " + BasePath
    # Определим, папка это или файл
    if os.path.isdir(BasePath):
        # работаем с каждым файлом в папке
        #for fil in sorted( os.listdir(BasePath) ):
        #    print "Renaming file %s\t" % fil
        #    # передадим полный путь к файлу
        #    rename( os.path.join(BasePath, fil) )
        # здесь лучше сделать os.walk
        for root, dirs, files in os.walk(BasePath):
            print "root: " + root
            for fname in files:
                if is_baikal( os.path.join(root,fname) ):
                    rename( os.path.join(root,fname) )
    else:
        # работаем с файлом
        if is_baikal(BasePath):
            rename(BasePath)
        
