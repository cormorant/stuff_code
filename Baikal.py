# -*- coding: utf-8 -*-

import struct
import numpy as np

#CANALS = ("NS", "EW", "Z", "NSg", "EWg", "Zg")

def stripnulls(s):
    """ очищает строку от символов пропуска и нулевых символов """
    return s.replace("\00", "").replace("\01", "").replace(".st", "").strip()


class BaikalFile():
    """ класс для файлов формата Байкал """
    # последний элемент кортежа - значение по умолчанию
    MainHeaderMap = (
        # назв          разм тип  знач. по умолч.
        ('kan',           2, "h", 0),#ends on 2 
        ('tip_test',      2, "h", 0),#4
        ('vers',          2, "h", 53),#6
        ('day',           2, "h", 1),#8
        ('month',        2, "h", 1),#10
        ('year',          2, "h", 1970),#12
        ('satellit',      2, "h", 0),#14
        ('valid',         2, "H", 12),#16
        ('pri_synhr',     2, "h", 0),#18
        ('PAZP',          2, "h", 24),#20
        ('reserv_short',  12, "6h", (0, 0, 0, 0, 0, 0)),#32
        ('station',       16, "16s", "_st"),#48
        ('dt',            8, 'd', 0.01), #56
        ('to',            8, 'd', 1.),#64
        ('deltas',        8, 'd', 0.),#72
        ('latitude',      8, 'd', 51.868),#80
        ('longitude',     8, 'd', 107.664),#88
        ('reserv_double', 16, '2d', (0, 0)),#104
        ('reserv_long',   16, '4I', (0, 0, 0, 0)),#120
    )
    ChannelHeaderMap = (
        ('phis_nom', 2, 'h'),                 #0 2
        ('reserv', 2*3, '3h'),                  #2-8
        ('name_chan', 24, '24s'),             #8 32, stripnulls
        ('tip_dat', 24, '24s'),               #32 56, stripnulls
        ('koef_chan', 8, 'd'),                #56 64
        ('calcfreq', 8, 'd'),                 #64 72
    )
    """ класс для файлов формата Байкал """
    def __init__(self, fname=None, headonly=False):
        if fname:
            # читаем существующий файл
            self.fname = fname
            self.MainHeader = None
            self.data = None
            # если файл является файлом формата Байкал - работаем с ним
            if self.is_baikal(fname):
                self.valid = True
                # если надо читать всё содержимое файла - это одно дело
                if not headonly:
                    try:
                        fil = open(fname, 'rb')
                        self.data = fil.read() # сохраним данные из файла
                        fil.close() # закроем файл
                    except IOError:
                        self.log("Error reading file " + fname)
                        sys.exit(1)
                    # считаем заголовок
                self.MainHeader = self.getMainHeader()
            else:
                self.valid = False
        else:
            # создаём файл с заголовком со значениями по умолчанию
            self.MainHeader = self._createEmptyMainHeader()
            self.data = None

    def _createEmptyMainHeader(self):
        ''' создаём заголовок со значениями по умолчанию '''
        pass
        #for fk in MainHeaderMap:
            

    def is_baikal(self, fname):
        """ является ли файлом формата Байкал """
        if fname[-3:].lower() == "prn":
            return# False
        # должно быть вразумительное число каналов
        try:
            with open(fname) as fil:  # файл открывается
                nkan = struct.unpack("h", fil.read(2))[0]
        except struct.error:
            print ("struct error at %s" % fname)
            return
        if not (nkan in range(1,7)):
            return
        return True
        
    def getMainHeader(self):
        """ считывание главного заголовка файла """
        # если у нас файл не считан, значит его надо открыть и читать оттуда 120 байт
        if self.data == None:
            with open(self.fname) as fil:  # файл открывается
                data = fil.read(120)
        else:
            # берём уже считанные данные. В пайтоне всё есть ссылка
            data = self.data
        # читаем и разбираем
        start = 0 # начальное смещение
        result = {}
        # считываем данные из главного заголовка
        for name, size, typ, _ in self.MainHeaderMap:
            result[name] = struct.unpack(typ, data[start:start+size])[0]
            start += size
        # поправим станцию
        result["station"] = stripnulls(result["station"])
        # неправильный год кое-где
        if result["year"] < 1900:
            result["year"] += 2000
        return result

    def getChannelHeader(self):
        """ считывание структуры CHANNEL_HEADER """
        start = 120 # адрес начала структур CHANNEL_HEADER
        result = []
        nkan = self.MainHeader['kan']
        for kan in range(nkan):
            r = {}
            # считывание i-го канала
            for c in self.ChannelHeaderMap:
                r[ c[0] ] = struct.unpack(c[2], self.data[start:start+c[1]])[0]
                start += c[1]
            result.append( stripnulls(r['name_chan']))#, r['koef_chan']) )
        #return ",".join(["%s:%f"%(k, v) for k, v in result.items()]), result
        return result

    def readData(self):#:, channels=0):
        ''' считывание мультиплексированных данных по каналам '''
        # сколько у нас каналов
        nkan = self.MainHeader['kan']
        # какие коэффициенты по каждому каналу
        ch_info = self.getChannelHeader()
        # размер одного замера
        razr = self.MainHeader["PAZP"]
        # где начинать считывать данные
        offset = 119+nkan*72+1# 336
        a = np.fromstring(self.data[offset:], dtype=np.int16 if razr==16 else np.int32)
        # демультиплексируем
        return a.reshape((len(a)/3, 3)).T
