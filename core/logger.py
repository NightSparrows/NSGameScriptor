
import datetime

from .util.serializeutil import SerializeUtil


class Logger:

    def info(msg):
        print('INFO [' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)              # 先這樣

    def warn(msg):
        print('WARN [' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
    
    def error(msg):
        print('ERROR[' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)

    def trace(msg):
        print('TRACE[' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
