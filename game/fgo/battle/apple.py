import cv2

from core.logger import Logger
from core.device.device import Device
from core.matchutil import MatchUtil

class Apple:

    s_appleWindow = cv2.imread('.//assets//fgo//battle//appleWindow.png')
    s_copperAppleImage = cv2.imread('.//assets//fgo//battle//copperApple.png')
    s_bronzeAppleImage = cv2.imread('.//assets//fgo//battle//bronzeApple.png')
    s_silverAppleImage = cv2.imread('.//assets//fgo//battle//silverApple.png')
    s_goldAppleImage = cv2.imread('.//assets//fgo//battle//goldApple.png')
    s_OKBtnImage = cv2.imread('.//assets//fgo//battle//ok.png')

    # 所有支援的蘋果 (黃金/白銀/青銅/赤銅果實)
    s_appleImages = {
        'gold': s_goldAppleImage,
        'silver': s_silverAppleImage,
        'bronze': s_bronzeAppleImage,
        'copper': s_copperAppleImage,
    }
    DEFAULT_SEQUENCE = ['gold']

    # 吃蘋果的優先順序, 前一種吃完/沒有才會用下一種; 空的代表不自動吃蘋果
    s_appleSequence = list(DEFAULT_SEQUENCE)

    # AP恢復視窗裡的道具清單區域 (top, bottom, left, right), 用來判斷清單有沒有捲動
    s_listRegion = (110, 570, 250, 1000)
    s_maxScroll = 8

    # 把設定檔/舊設定檔的 apple 欄位整理成蘋果種類的 list
    # 舊版設定檔是單一字串 (例如 'gold'), 新版是 list (例如 ['bronze', 'silver'])
    def normalizeSequence(value) -> list:
        if value is None:
            return list(Apple.DEFAULT_SEQUENCE)
        if isinstance(value, str):
            value = [value]

        sequence = []
        for appleType in value:
            if appleType not in Apple.s_appleImages:
                Logger.warn('Unknown apple type: ' + str(appleType))
            elif appleType not in sequence:
                sequence.append(appleType)
        return sequence

    def checkAppleWindow(device: Device):

        Logger.info('Checking apple window...')
        result, _ = MatchUtil.WaitFor(device, Apple.s_appleWindow, 2)

        if not result:
            Logger.info('No apple window')
            return False
        else:
            Logger.info('Having apple window, Eat apple')
            if not Apple.eatApple(device, Apple.s_appleSequence):
                Logger.error('Failed to eat apple')
                return False
            return True


    # appleType: 蘋果種類, 或是依優先順序排列的蘋果種類 list
    def eatApple(device: Device, appleType = 'gold'):

        sequence = Apple.normalizeSequence(appleType)
        if not sequence:
            Logger.error('No apple type is set to eat')
            return False

        for apple in sequence:
            Logger.info('Trying apple: ' + apple)
            if Apple._eatOne(device, apple):
                Logger.info('Ate apple: ' + apple)
                return True
            Logger.info('Apple ' + apple + ' is not available')

        Logger.error('No apple in the sequence is available')
        return False

    # 吃一種蘋果: 先捲回清單頂端, 再一頁一頁往下找圖示, 點下去後要出現確認視窗才算吃成功
    # (沒有的蘋果點下去不會出現確認視窗)
    def _eatOne(device: Device, appleType: str) -> bool:

        template = Apple.s_appleImages[appleType]

        Apple._scrollList(device, up=True)
        for _ in range(Apple.s_maxScroll):
            device.screenshot()
            result = MatchUtil.match(device.getScreenshot(), template)
            if MatchUtil.isMatch(result, 0.9):
                point = MatchUtil.calculated(result, template.shape)
                device.tap(point['x']['center'], point['y']['center'])
                device.sleep(0.7)

                device.screenshot()
                if MatchUtil.isMatch(MatchUtil.match(device.getScreenshot(), Apple.s_OKBtnImage)):
                    Logger.info('Has OK window')
                    return MatchUtil.TapImage(device, Apple.s_OKBtnImage)

                Logger.warn('No OK window while tap apple ' + appleType)
                return False

            # 這一頁沒有, 往下捲, 捲不動就是到底了
            if not Apple._scrollList(device, up=False, once=True):
                break

        return False

    # 捲動道具清單; once=False 會一直捲到清單不再變化為止 (捲到頂/底)
    # 回傳有沒有捲動過
    def _scrollList(device: Device, up: bool, once: bool = False) -> bool:
        top, bottom, left, right = Apple.s_listRegion

        device.screenshot()
        prev = device.getScreenshot()[top:bottom, left:right]
        moved = False
        for _ in range(1 if once else Apple.s_maxScroll):
            if up:
                device.holdScroll(640, 200, 640, 500, 500)
            else:
                device.holdScroll(640, 500, 640, 200, 500)
            device.sleep(0.8)

            device.screenshot()
            cur = device.getScreenshot()[top:bottom, left:right]
            if float(cv2.absdiff(prev, cur).mean()) <= 0.5:
                break
            moved = True
            prev = cur

        return moved
