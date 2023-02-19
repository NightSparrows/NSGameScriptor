
import cv2

from core.logger import Logger

from core.game.game import Game

from core.device.device import Device
from core.matchutil import MatchUtil

class GameBlueArchive(Game):

    def __init__(self, device: Device) -> None:
        super().__init__('BlueArchive')
        self._device = device
    
    def execute(self):


        raise NotImplementedError('Game ' + self.m_name + ' execute not impl')

    def restart(self):

        self._device.killApp('com.nexon.bluearchive')
        result = self._device.openApp('com.nexon.bluearchive/.MxUnityPlayerActivity')

        Logger.trace(str(result))

        # TODO 進入大廳

        # 確認活動screen跳過
        Logger.info('確認有無活動畫面...')
        iconImage = cv2.imread('assets/bluearchive/login/startIcon.png')
        if not MatchUtil.pressUntilAppear(self._device, iconImage, 100, 687, 60):
            Logger.error('Failed to 認得開始介面')

        # touch to start
        Logger.info('正在關閉開始畫面...')
        if not MatchUtil.pressUntilDisappear(self._device, iconImage, 640, 120, 60):
            Logger.error('Failed to 關閉開始介面')

        # 把公告關掉
        annImage = cv2.imread('assets/bluearchive/login/announcementText.png')

        MatchUtil.setWaitInterval(0.5)
        Logger.info('等待公告畫面秀出...')
        have, result = MatchUtil.WaitFor(self._device, annImage, 30)
        MatchUtil.setWaitInterval(1)

        if not have:
            Logger.warn('Not found 公告 window')
        else:
            MatchUtil.pressUntilDisappear(self._device, annImage, 1178, 117, 2)

        # in 大廳

        # change state to lobby
        raise NotImplementedError('Game ' + self._name + ' restart not impl.')
