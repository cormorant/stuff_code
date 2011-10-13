#!/usr/bin/env python
#coding: utf-8

"""
Здесь собираем готовые алгоритмы для работы с тектономагнитными данными.
Модульные и векторные данные.
"""

import os, sys

import numpy as np
import scikits.timeseries as ts
#import StringIO
import datetime, array


Mdtype = [('field', float), ('time','S6')]
Vdtype = [('dates', int), ('h', float), ('d', float), ('z', float), ('f', float),]

def module_series_from_txt(fname):
    "Загрузка модульных данных их исходных текстовых файлов"
    data = np.loadtxt(fname, usecols=(0, 1), dtype=Mdtype)
    dt = []
    values = array.array('f')
    for d in data:
        if d['field'] == 0: date = d['time']
        else:
            dt.append('%s %s' % (date, d['time']))
            values.append(d['field'])
    dt = map(lambda s: datetime.datetime.strptime(s, '%y%m%d %H%M%S'), dt)
    series = ts.time_series(values, dates=dt, freq="T")
    return series


def vector_series_from_txt(fname, COLS = "FHDZT"):
    """ Загружаем векторные данные из списка файлов """
    # наш тип данных - пока только первые три столбца
    DTYPE = [('date', 'S6'), ('time', 'S6'), ('st', float)]
    # определим сколько столбцов в файле и что загружатьn_col = get_column_count(fname)
    # определим тип данных, добавим столбцы со значениями
    for col in COLS:
        DTYPE.append( (col, float) )
    # загрузим файл
    data = np.loadtxt(fname, dtype= DTYPE)
    # create datetime list
    dates = map(lambda d, t: datetime.datetime.strptime("%s %s" % (d ,t), '%y%m%d %H%M%S'),
        data["date"], data["time"])
    return ts.time_series(
        zip( data["F"], data["H"], data["D"], data["Z"] ),
        dates=dates, dtype=DTYPE[:-1]
    )

def vector_series_from_txt2(fname, col=3):
    """ Возвращает один запрашенный столбец со значениями """
    data = np.loadtxt(
        fname,
        usecols=(0, 1, col),#6-x(d), 4-y(h), 5-z
        dtype=[('date', 'S6'), ('time', 'S6'), ('field', float)]# + DTYPE
    )
    """
    dates = ts.date_array( dlist = [ ts.Date('T', string="%s %s" % (d, t)) \
        for d, t in zip(data['date'], data['time']) ] )
    """
    #dates
    dates = ["%s %s"%(d, t) for d, t in zip(data['date'], data['time'])]
    dates = map(lambda s: datetime.datetime.strptime("%s" % s, '%y%m%d %H%M%S'), dates)
    # промежуточная серия
    return ts.time_series(data['field'], dates=dates, freq="T")
    """
    series_list.append( s )
    #
    values = np.empty(len(series), dtype=desctype)
    values['dates'] = series.dates
    values['h'] = series['h']._data
    values['d'] = series['d']._data
    values['z'] = series['z']._data
    values['f'] = series['f']._data
    """

#Graphics
def plot_ts(series, lib="matplotlib"): #*args
    if lib == "matplotlib":
        import matplotlib.pyplot as plt
        import scikits.timeseries.lib.plotlib as tpl
        fig = tpl.tsfigure()
        fsp = fig.add_tsplot(111)
        fsp.tsplot(series, '-')
        plt.show()
    else:
        # guiqwt
        #raise NotImplementedError
        pass

def get_irt_data(date1, date2):
    import sqlite3
    from scipy.signal import medfilt
    DB_FILE = "/home/Work/magn/IRT.sqlite"
    try:
        conn = sqlite3.connect(DB_FILE)
    except OperationalError:
        print "Cannot find database!"
        return
    cursor = conn.cursor()
    # считываем
    cursor.execute("""
        SELECT intdt, f
        FROM irt_vectordata WHERE intdt BETWEEN ? AND ?
        ORDER BY intdt ASC
        """, (
            ts.Date('T', datetime=date1).value,#series.dates[0].datetime).value,
            ts.Date('T', datetime=date2).value+1,
        )
    )
    #print date1, date2
    _dates, _values = zip(*cursor.fetchall())
    conn.close()
    #print "get series from values and dates"
    series = ts.time_series(medfilt(_values), dates=_dates, freq='T')
    # скроем пропуски = 99999.0
    series[(series==99999)]=np.ma.masked
    return series.compressed()






"""
try:
    from tektmagn import plot_ts
except ImportError:
    sys.path.append("/home/petr/local/python/lib/")
    from tektmagn import plot_ts


def smooth(x, window_len=7, window='flat'):
    s=np.r_[2*x[0] - x[window_len:1:-1], x, 2*x[-1] - x[-1:-window_len:-1]]
    w=np.ones(window_len, 'd')
    y=np.convolve(w/w.sum(), s, mode='same')
    return y[window_len-1 : -window_len+1]

"""

