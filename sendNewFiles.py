#!/usr/bin/env python
#coding: utf-8
""" Программа отправки по ftp файлов, выделенных программой регистрации a2009_reg.exe """
import threading
import datetime#, time
import zipfile
import os, sys
import ftplib

#sys.stdout = open("log.txt","w")
#sys.stderr = open("errlog.txt","w")

ConfigFile = 'send.conf'
# Читаем настройки из файла
Settings = {}
for line in open(ConfigFile):
    if line[0] == '#': continue
    # слева от знака = ключ, справа значение
    if line:
        pair = line.split('=')
        Settings[ pair[0].strip() ] = pair[-1].strip()

# словарь: настройка и значение по умолчанию
SettingsDict = {
    'STATION': 'ST',
    #'AngaraDir': os.path.realpath( os.path.dirname(__file__) ), # папка откуда запущена программа
    'INTERVAL': 5*60, # 5 минут
    'SIGN': '!', # что искать в названии файла
    'ADDRESS': '84.237.30.24', # адрес куда отправлять на ftp
    'FTPDIR': 'Station', # в какую папку складывать файлы
    'ZIPDIR': 'zip', # куда сохранять архивы
}

# Возъмем из настроек нужные значения
for k in SettingsDict.keys():
    if not Settings.has_key(k):
        Settings[k] = SettingsDict[k]


class SendFiles():
    def __init__(self, Dir=None):
        """ При создании класса ... """
        # откуда запущен скрипт
        self.CurrDir = AngaraDir
        print "Current Dir is " + self.CurrDir
        # сегодняшнее число
        print "Started at", datetime.datetime.today()
        # список уже отправленных файлов
        self.sent_files = self.get_send_files()
        # счётчик запусков
        self.i = 0

    def get_send_files(self):
        # Запомним список уже созданных при запуске файлов со знаком (!),
        # их отправлять не будем
        sent_files = []
        for root, dirs, files in os.walk( self.CurrDir ):
            for fname in files:
                if SIGN in fname:
                    sent_files.append( os.path.join(root, fname) )
        return sent_files
    
    def setup_connection(self):
        """ устанавливает соединение с интернетАм """
        print 'connecting by rasdial...'
        # Огородить Try-ями и ексепшенами необходимо!
        os.system('rasdial megafon')

    def disconnect(self):
        """ Разрывает модемное соединение под Windows XP """
        print 'Disconnecting...'
        os.system('rasdial /DISCONNECT')

    def run(self):
        """ Функция запускается всё время работы программы,
        а по завершении -- до тех пор пока не отработает последний поток. 
        При запуске создаётся список существующих файлов, при каждом
        следующем запуске проверяется наличие новых и есть ли
        в их расширении искомый знак (!) """
        self.i += 1
        print datetime.datetime.today()
        # найти все новые выделенные файлы
        to_send = [fil for fil in self.get_send_files() if fil not in self.sent_files]
        #print "TO send: ", to_send
        if to_send:
            # установим соединие
            self.setup_connection()
            # отправляем файлы отдельно каждый в архиве
            for fil in to_send:
                strip_fil = os.path.split(fil)[-1].strip('!')
                # название архива - имя файла без воскл знака (добавлять ли STATION+fname)
                zipname = os.path.join( self.CurrDir, ZIPDIR, STATION+strip_fil+".zip" )
                z = zipfile.ZipFile(zipname, "w", zipfile.ZIP_DEFLATED)
                # полный путь и как будем называться в архиве
                z.write( fil, os.path.split(fil)[-1] )
                z.close()
                # отправляем файл по ftp
                print "sending file %s" % zipname
                try:
                    conn = ftplib.FTP(ADDRESS, 'seismol', 'seismol')
                except: # какое исключение (?)
                    print "Error with connection"
                    break
                conn.cwd(FTPDIR)
                fil_send = open(zipname, 'rb')
                try:
                    conn.storbinary('STOR %s' % os.path.split(zipname)[-1], fil_send)#,1024)
                except:# error_perm:
                    print 'Error with permission while sending file'
                finally:
                    print "sending completed"
                fil_send.close()
                # добавить файл в список отправленных
                self.sent_files.append(fil)
            # Все файлы отправлены - разорвём соединение
            self.disconnect()
        #else:
        #    print "Nothing to send"
        
        print 'Completed attempt %s at %s' % (self.i, datetime.datetime.today())
        # 3 строки пропустим
        print "\n"*3
        # Запустим следующий поток
        # function runs every N(Interval) second
        threading.Timer(1.0*INTERVAL, self.run).start()

if __name__ == "__main__":
    # проверим наличие указанной папки с файлами
    if not os.path.exists( AngaraDir ):
        print "Error! Invalid path %s." % AngaraDir
        sys.exit(1)
    # налчичие папки для архивов
    if not os.path.exists( os.path.join(AngaraDir, ZIPDIR) ):
        os.mkdir( os.path.join(AngaraDir, ZIPDIR) )
    # создадим наш объект
    send_files = SendFiles()
    # через 1 секунду начнём 1-й поток
    threading.Timer(1.0, send_files.run).start()
