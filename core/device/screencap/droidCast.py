
import numpy as np
import cv2
import requests
import time
import os
import socket

from core.base import Base

from .screencap import ScreenCap

from ...logger import Logger

EXCLUDED_RANGES = [
    (50000, 50059),
    (53477, 53576),
    (54578, 54677),
    (54678, 54777),
    (54778, 54877),
    (54878, 54977),
    (54978, 55077),
    (55078, 55177),
    (55178, 55277),
    (55278, 55377),
]

def is_port_available(port: int) -> bool:
    """檢查本地 port 是否可以綁定"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

def find_free_port(start_port=55600) -> int:
    port = start_port
    while True:
        # 跳過 Windows 保留 port 範圍
        if any(start <= port <= end for (start, end) in EXCLUDED_RANGES):
            port += 1
            continue
        # 檢查 port 是否被佔用
        if is_port_available(port):
            return port
        port += 1

class droidCast(ScreenCap):
    
    DROIDCAST_FILEPATH_LOCAL = './bin/DroidCast/droidCast_raw.apk'
    DROIDCAST_FILEPATH_REMOTE = '/data/local/tmp/DroidCast_raw.apk'

    def __init__(self, device) -> None:
        # install ascreencap into emulator
        self._device = device

        # 檢查 DroidCast 是否已啟動
        self._port = None
        (returncode, stdout, _) = self._device.run_adb(['shell', 'ps', '-ef'])
        if returncode == 0:
            for line in stdout.splitlines():
                if 'app_process' in line and droidCast.DROIDCAST_FILEPATH_REMOTE in line:
                    # 找到已啟動的 DroidCast
                    parts = list(filter(None, line.split(' ')))
                    pid = parts[1]
                    # 嘗試從 process args 解析 port
                    import re
                    match = re.search(r'--port=(\d+)', line)
                    if match:
                        self._port = int(match.group(1))
                        Logger.trace(f"Found existing DroidCast pid[{pid}] using port {self._port}")
                        break

        if self._port is None:
            # DroidCast 尚未啟動，找空閒 port
            self.stop()  # 先清理殘留 process
            self._port = find_free_port()  # 找空閒 port

            # 檢查 APK
            local_size = os.path.getsize(droidCast.DROIDCAST_FILEPATH_LOCAL)
            (returncode, stdout, _) = self._device.run_adb([
                "shell", "stat -c%s " + droidCast.DROIDCAST_FILEPATH_REMOTE
            ])
            remote_size = int(stdout.strip()) if returncode == 0 else -1
            if local_size != remote_size:
                Logger.info('DroidCast APK size mismatch, pushing to emulator')
                self._device.run_adb(['push', droidCast.DROIDCAST_FILEPATH_LOCAL, droidCast.DROIDCAST_FILEPATH_REMOTE])
            else:
                Logger.trace('DroidCast APK already exists and matches size, skipping push')

            # run droid cast in emulator
            args = ["shell",
                    "app_process",
                    '-Djava.class.path=%s' % droidCast.DROIDCAST_FILEPATH_REMOTE,
                    '/',
                    "com.rayworks.droidcast.Main",
                    "--port=%d" % self._port,
                    ">",
                    "/dev/null",
                    "&"]
                    
            # args = ["shell",
            #         class_path,
            #         "app_process",
            #         "/",  # unused
            #         "com.rayworks.droidcast.Main",
            #         "--port=%d" % self._port]
            self._device.run_adb_dontcare(args)
            Logger.trace('Run droidcast in background')

            # forward tcp the adb to host
            (code, _, err) = self._device.run_adb(["forward", "tcp:%d" % self._port, "tcp:%d" % self._port])
            Logger.trace(">>> adb forward tcp:%d %s" % (self._port, code))



        #thread = threading.Thread(target=self.droidCastFun, args=(class_path,))
        #thread.start()
        self._session = requests.Session()
        self._session.trust_env = False


    def screenshot(self) -> bool:
        
        startTime = time.time()
        url = 'http://localhost:%d/screenshot' % (self._port)

        try:
            response = self._session.get(url, timeout=3, stream=True)
            raw_image = b''.join(response.iter_content(chunk_size=8192))
            response.close()
        except Exception as e:
            Logger.error(f'Failed to fetch screenshot using droidCast: {e}')
            return False

        # raw_image = self._session.get(url, timeout=3).content

        durTime = time.time() - startTime
        #Logger.trace('Screenshot takes ' + str(durTime) + ' secs')

        img_array = np.asarray(bytearray(raw_image), dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        self._screenshot = image

    def getScreenshot(self):
        return self._screenshot

    def screenshot_save(self):
        self.screenshot()

        cv2.imwrite('screenshot.png', self._screenshot)

        Logger.trace('Img saved.')

        return

    def stop(self):
        # find droidcast process
        (returncode, stdout, _) = self._device.run_adb(['shell', 'ps', '-ef'])

        if (returncode != 0):
            return

        splitStr = stdout.split('\n')

        for line in splitStr:
            processInfo = list(filter(None, line.split(' ')))
            if len(processInfo) < 1:
                continue
            #print('pid: ' + processInfo[1])
            #print('name: ' + processInfo[7])

            if 'app_process' in line and droidCast.DROIDCAST_FILEPATH_REMOTE in line:
            # if processInfo[7] == 'app_process' and processInfo[8] == ('-Djava.class.path=%s' % droidCast.DROIDCAST_FILEPATH_REMOTE):
                self._device.run_adb(['shell', 'kill', processInfo[1]])
                print('droidcast pid[' + processInfo[1] + '] killed')
        return
