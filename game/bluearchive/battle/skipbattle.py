
import time

from core.logger import Logger
from core.matchutil import MatchUtil
from core.device.device import Device

from game.bluearchive.asset import Asset

class SkipBattle:

    # 0
    # 1 沒有AP
    # 2 次數不足

    def execute(device: Device, count: int):

        result, _ = MatchUtil.WaitFor(device, Asset.questInfoWindowIconImage, 3)

        if not result:
            Logger.error('[SkipBattle] Quest info window not found.')    
            return False, 0
        
        # 按3次
        for i in range(count - 1):
            device.tap(1035, 300)
            time.sleep(0.5)

        # 按掃蕩開始
        time.sleep(1)
        device.tap(870, 403)
        time.sleep(1)

        # 沒有AP
        if MatchUtil.Having(device, Asset.buyAPWindowImage):
            Logger.warn('[SkipBattle] 沒有AP')
            return False, 1

        # 次數不足
        if MatchUtil.Having(device, Asset.notEnoughInfoImage):
            Logger.warn('[TASK][SkipBattle] 困難 已打完')
            return True, 2

        # 按確認
        if not MatchUtil.pressUntilDisappear(device, Asset.infoWindowIconImage, 765, 500, 5):
            Logger.error('[TASK][HardQuest] 無法按\'確認\'開始掃蕩')

        # 按skip
        device.tap(640, 500)
        # 等到掃蕩結束

        while not MatchUtil.Having(device, Asset.confirmBtnImage):
            time.sleep(1)

        # 按確定
        device.tap(640, 580)
        time.sleep(1)
        # End Skip battle 範圍


