
import os
import shutil
import sys


class Base:

    s_toolkitPath = '../toolkit'

    # cross-platform adb binary resolution: prefer a bundled copy under
    # s_toolkitPath (the historical Windows setup, toolkit/adb/adb.exe)
    # when present, otherwise fall back to whatever 'adb'/'adb.exe' is on
    # PATH (the normal case on Linux, and also works on Windows if adb is
    # installed system-wide e.g. via Android SDK platform-tools).
    @staticmethod
    def getAdbPath() -> str:
        exeName = 'adb.exe' if sys.platform == 'win32' else 'adb'
        bundled = Base.s_toolkitPath + '/adb/' + exeName
        if os.path.isfile(bundled):
            return bundled

        found = shutil.which(exeName) or shutil.which('adb')
        if found:
            return found

        return exeName
