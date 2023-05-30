
import time
import cv2

from core.logger import Logger
from core.device.device import Device

from .battletask import BattleTask
from .battledata import BattleData

from core.matchutil import MatchUtil

class CardBattleTask(BattleTask):

    s_atkBtnImage = cv2.imread('.//assets//fgo//battle//attackBtn.png')
    def __init__(self, data: BattleData, cards) -> None:
        self._cards = cards
        self._data = data
        assert(len(cards) == 3)

    def execute(self):
        
        # 按attack進入選卡
        _, result = MatchUtil.WaitFor(self._data.device, CardBattleTask.s_atkBtnImage, 5)

        if result == None:
            Logger.info('Failed to check attack button')
            return False
        
        time.sleep(1)
        MatchUtil.PressUntilColorChange(self._data.device, result['max_loc'][0], result['max_loc'][1], 3)
        time.sleep(1)

        chosenCard = [False, False, False, False, False]
        for i in range(3):
            cardCmd = self._cards[i]

            if cardCmd[0] == 'c':   # 寶具
                charNo = int(cardCmd[1])
                cardX = 140 + (charNo * 250)
                self._data.device.tap(cardX, 220)
                Logger.info('Choose 寶具' + str(charNo))
            elif cardCmd[0] == 'r':           # 隨便選
                for j in range(5):
                    if (chosenCard[j]):
                        continue
                    cardX = 140 + (j * 250)
                    self._data.device.tap(cardX, 500)
                    Logger.info('Choose random ' + str(j))
                    chosenCard[j] = True
                    break
            else:
                Logger.error('Card script syntax error')
                return False
            
            time.sleep(0.3)

        return True





