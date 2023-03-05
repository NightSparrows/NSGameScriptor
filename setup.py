
import os

from core.base import Base
import subprocess

if __name__ == '__main__':

    subprocess.check_output(Base.s_toolkitPath + '/adb/adb.exe kill-server')
    subprocess.check_output(Base.s_toolkitPath + '/adb/adb.exe start-server')

    result = subprocess.check_output(Base.s_toolkitPath + '/adb/adb.exe devices')

    result = result.replace(b'\r\n', b'\n').decode('utf-8')

    print(result)

    deviceName = input('輸入模擬器名稱>')

    configData = dict()

    configData['device'] = deviceName

    try:
        
        if not os.path.exists('./config'):
            os.makedirs('./config')
            
        f = open('./config/config.json', 'w')
        f.write(configData)
        print('儲存成功')
    except:
        print('無法寫入設定檔')
    finally:
        f.close()
