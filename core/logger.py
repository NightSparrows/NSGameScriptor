
import datetime
from colorama import Fore, Back, init

from .util.serializeutil import SerializeUtil

init(autoreset=True)

class Logger:

    # optional external listeners, e.g. a GUI log panel.
    # each listener is called as fn(level: str, msg: str), level in {'info','warn','error','trace'}
    _listeners = []

    def addListener(fn):
        if fn not in Logger._listeners:
            Logger._listeners.append(fn)

    def removeListener(fn):
        if fn in Logger._listeners:
            Logger._listeners.remove(fn)

    def _notify(level, msg):
        for fn in Logger._listeners:
            try:
                fn(level, msg)
            except Exception:
                pass

    def info(msg):
        print(Fore.CYAN + 'INFO [' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)              # 先這樣
        Logger._notify('info', msg)

    def warn(msg):
        print(Fore.YELLOW + 'WARN [' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
        Logger._notify('warn', msg)

    def error(msg):
        print(Fore.RED + 'ERROR[' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
        Logger._notify('error', msg)

    def trace(msg):
        print(Fore.LIGHTCYAN_EX + 'TRACE[' + SerializeUtil.GetStringFromDateTime(datetime.datetime.now()) + ']: ' + msg)
        Logger._notify('trace', msg)
