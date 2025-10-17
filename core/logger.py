
import datetime
from colorama import Fore, Back, init

from .util.serializeutil import SerializeUtil

init(autoreset=True)

class Logger:

    def info(msg):
        print(Fore.CYAN + 'INFO [' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)              # 先這樣

    def warn(msg):
        print(Fore.YELLOW + 'WARN [' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
    
    def error(msg):
        print(Fore.RED + 'ERROR[' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)

    def trace(msg):
        print(Fore.LIGHTCYAN_EX + 'TRACE[' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
