
import time
import cv2

from core.logger import Logger
from core.device.device import Device

from .battletask import BattleTask
from .battledata import BattleData

from core.matchutil import MatchUtil

class CardBattleTask(BattleTask):

    s_atkBtnImage = cv2.imread('.//assets//fgo//battle//attackBtn.png')
    def __init__(self, data: BattleData, cmdArgs: list) -> None:
        self._cards = list()
        for i in range(1, len(cmdArgs)):
            self._cards.append(cmdArgs[i])

        self._data = data

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
        numberOfCardChoosed = 0
        i = 0
        while numberOfCardChoosed < 3:
            cardCmd = self._cards[i]

            if cardCmd[0] == 'c':   # 寶具
                charNo = int(cardCmd[1])
                cardX = 140 + (charNo * 250)
                self._data.device.tap(cardX, 220)
                Logger.info('Choose 寶具' + str(charNo))
                numberOfCardChoosed += 1
            elif cardCmd[0] == 'r':           # 隨便選
                for j in range(5):
                    if (chosenCard[j]):
                        continue
                    cardX = 140 + (j * 250)
                    self._data.device.tap(cardX, 500)
                    Logger.info('Choose random ' + str(j))
                    chosenCard[j] = True
                    numberOfCardChoosed += 1
                    break
            elif cardCmd[0] == 't':         # 打手卡
                for j in range(5):
                    if (chosenCard[j]):
                        continue
                    if len(cardCmd) == 1:
                        cardX = 140 + (j * 255)
                        if (MatchUtil.HavinginRange(self._data.device, self._data._thugImage, cardX - 100, 380, 170, 240)):
                            self._data.device.tap(cardX, 500)
                            Logger.info('Choose thug card ' + str(j))
                            chosenCard[j] = True
                            numberOfCardChoosed += 1
                            break
            else:
                Logger.error('Card script syntax error')
                return False
            
            time.sleep(0.3)
            i += 1

        return True





