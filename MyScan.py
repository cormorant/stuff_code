#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SYNOPSIS: scan [-f ФОРМАТ] [OPTIONS] dir1 dir2 dir3 ...

Искать по всем указанным файлам/каталогам, определить, где есть данные для станций
и на каких отрезках времени.
Начало каждого файла отмечено крестиками, пропуски указаны вертикальными красными линиями.
Частота дискретизации должна оставаться одинаковой для каждой станции, но могут варьироваться в зависимости от
станций.

Каталоги могут также использоваться в качестве аргументов. Они будут отсканированы рекурсивно.
Подробная информация выводится с "-V".

Поддерживаемые форматы: все форматы, поддерживаемые ObsPy модулей
(в настоящее время: MSEED, GSE2, SAC, SACXY, WAV, SH-АСК, SH-Q, SEISAN).
Если формат заранее известно, скорость чтения можно увеличить явно указав формата файла ("-f ФОРМАТ"),
в противном случае формат определяется автоматически.
"""
activate_this = '/home/petr/local/virtual/OBS/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys
import os
import datetime

#from obspy.core import read, 
from obspy.core import UTCDateTime, AttribDict, Stream, Trace
from obspy.mseed.core import readMSEED

from optparse import OptionParser
from matplotlib.dates import date2num
from matplotlib.pyplot import figure, show
from matplotlib.pylab import rcParams, DateFormatter

"""
rcParams[font.sans-serif = Verdana
xtick.labelsize = 8
ytick.labelsize = 8
figure.facecolor = white
axes.facecolor = white
"""

import numpy as np

from Baikal import BaikalFile


def parse_file_to_dict(data_dict, samp_int_dict, file, counter, format=None, verbose=False):
    """ Читаются файлы в своих форматах, отуда вытаскивается информация о времени """
    # если формат не указан - это miniseed
    if format == None:
        try:
            stream = readMSEED(file, headonly=True)
        except:
            print("Can not read %s" % (file))
            return counter
    else:
        # у нас формат БАЙКАЛ
        bf = BaikalFile(file, headonly=True)
        # правильный ли файл
        if not bf.valid:
            print("Skipping file %s" % file)
            return counter
        Header = bf.MainHeader
        # заголовок
        hour, minute, seconds = datetime.timedelta(seconds=Header["to"]).__str__().split(":")
        header = {
            'network': 'BFG',
            'station': Header['station'][:3],
            'location': '',
            'channel': "0",
            'npts': 30000,# файлы обычно по 5 минут
            #'mseed': {'dataquality': 'D'},
            'starttime': UTCDateTime(
                Header["year"], #2009,
                Header["month"], #8,
                Header["day"], #24,
                int(hour), #0,
                int(minute), #20,
                float(seconds), #3,
            ),
            'sampling_rate': 1/Header['dt'],
        }
        # добавить канал (один для всех)
        trace = Trace(header=header)#, data=)
        # работаем в терминах obspy
        stream = Stream(traces=[trace])
    s = "%s %s" % (counter, file)
    if verbose:
        sys.stdout.write("%s\n" % s)
        for line in str(stream).split("\n"):
            sys.stdout.write("    " + line + "\n")
    else:
        sys.stdout.write("\r" + s)
        sys.stdout.flush()
    for tr in stream:
        _id = tr.getId()
        data_dict.setdefault(_id, [])
        data_dict[_id].append([date2num(tr.stats.starttime), date2num(tr.stats.endtime)])
        samp_int_dict.setdefault(_id, 1.0 / (24 * 3600 * tr.stats.sampling_rate))
    return (counter + 1)

def recursive_parse(data_dict, samp_int_dict, path, counter, format=None, verbose=False):
    """ Рекурсивная обработка файлов """
    if os.path.isfile(path):
        counter = parse_file_to_dict(data_dict, samp_int_dict, path, counter, format, verbose)
    elif os.path.isdir(path):
        for file in (os.path.join(path, file) for file in os.listdir(path)):
            counter = recursive_parse(data_dict, samp_int_dict, file, counter, format, verbose)
    else:
        print "Problem with filename/dirname: %s" % (path)
    return counter


def main():
    parser = OptionParser()#__doc__.strip())
    parser.add_option(
        "-f", "--format", default=None,
        type="string", dest="format",
        help="Optional, the file format."
    )
    parser.add_option(
        "-v", "--verbose", default=False,
        action="store_true", dest="verbose",
        help="Optional. Verbose output."
    )
    (options, args) = parser.parse_args()
    
    if len(args) == 0:
        parser.print_help()
        sys.exit(1)

    fig = figure()
    ax = fig.add_subplot(111)
    # station
    data = {}
    samp_int = {}
    counter = 0
    for path in args:
        counter = recursive_parse(
            data, samp_int, path, counter,
            options.format, options.verbose,
        )

    if not data:
        print("Нет данных!")
        return
    #
    # Loop throught this dictionary
    ids = sorted(data.keys())
    for _i, _id in enumerate(ids):
        data[_id].sort()
        startend = np.array(data[_id])
        offset = np.ones(len(startend)) * _i #generate list of y values
        ax.plot_date(startend[:, 0], offset, 'x', linewidth=2)
        ax.hlines(offset, startend[:, 0], startend[:, 1])
        # найти даты
        diffs = startend[1:, 0] - startend[:-1, 1] #currend.start - last.end
        
    ax.set_ylim(0 - 0.5, _i + 0.5)
    ax.set_yticks(np.arange(_i + 1))
    ax.set_yticklabels(ids)
    fig.autofmt_xdate() #rotate date
    show()
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
