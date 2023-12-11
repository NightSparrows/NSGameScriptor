
import datetime
from colorama import Fore, Back

from .util.serializeutil import SerializeUtil


class Logger:

    def info(msg):
        print(Fore.BLUE + 'INFO [' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)              # 先這樣

    def warn(msg):
        print(Fore.YELLOW + 'WARN [' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
    
    def error(msg):
        print(Fore.RED + 'ERROR[' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)

    def trace(msg):
        print(Fore.WHITE + 'TRACE[' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
