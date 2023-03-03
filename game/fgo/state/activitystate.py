

import time

import cv2

from core.logger import Logger
from core.device.device import Device
from core.game.state import State
from core.game.gamedata import GameData

from core.matchutil import MatchUtil

from game.fgo.asset import Asset

# TODO
class ActivityState(State):

    def __init__(self, device: Device, data: GameData, activityConfig) -> None:
        super().__init__('Activity')
        self._data = data
        self._device = device
        self._config = activityConfig
        self._activityName = activityConfig['current']
        self._enterBtnImage = cv2.imread(activityConfig['button'])

        assetPath = './assets/fgo/activity/' + activityConfig['current']

        self._levels = dict()
        for level in activityConfig['level']:
            levelName = level['name']
            image = cv2.imread(assetPath + '/' + levelName + '.png')
            levelData = dict()
            levelData['image'] = image
            levelData['position'] = level['position']
            levelData['appName'] = level['appName']
            levelData['level'] = level['level']
            self._levels[levelName] = levelData

    def gotoLevel(self, levelName: str):

        assert(self._data.currentState == self.getName())

        levelData = self._levels[levelName]
        if levelData == None:
            Logger.error('Unknown level name: ' + levelName)
            return False
        

        # find the current position
        currentPosX = -100
        currentPosY = -100
        while True:
            for key in self._levels:
                keyLevelData = self._levels[key]
                self._device.screenshot()
                screenshot = self._device.getScreenshot()
                result = MatchUtil.match(screenshot, keyLevelData['image'])

                if not MatchUtil.isMatch(result):
                    continue

                # match
                currentPosX = keyLevelData['position'][0] - result['max_loc'][0]
                currentPosY = keyLevelData['position'][1] - result['max_loc'][1]
                break

            if currentPosY == -100 or currentPosX == -100:
                Logger.error('Failed to find current position')
                # TODO 先回到左上角
                continue
            else:
                break
        
        wishPosX = levelData['position'][0] - 640
        wishPosY = levelData['position'][1] - 360

        timer = 0
        inLevel = False
        while timer <= 30:
            
            if MatchUtil.TapImage(self._device, levelData['image']):
                inLevel = True
                break

            if currentPosX > wishPosX:
                swipeX = 320
            elif currentPosX < wishPosX:
                swipeX = -320
            else:
                swipeX = 0
            
            if currentPosY > wishPosY:
                swipeY = 180
            elif currentPosY < wishPosY:
                swipeY = -180
            else:
                swipeY = 0
            
            self._device.holdScroll(640, 360, 640 + swipeX, 360 + swipeY, 900)
            time.sleep(2)
            currentPosX -= swipeX
            currentPosY -= swipeY
            timer += 1
        
        if not inLevel:
            Logger.error('Failed to enter level')
            return False
        

        return True
            

    def goback(self):
        assert(self._data.currentState == self.getName())

        if not MatchUtil.TapImage(self._device, Asset.BackToLobbyBtnImage):
            Logger.error('Failed to tap 管制室 button')
            return False
        
        return True


    def enter(self):
        assert(self._data.currentState == self.getParentName())

        if self._config['current'] == 'None':
            Logger.error('現在沒有活動')
            return False

        # 回到最上面
        self._device.tap(1247, 148)
        time.sleep(1)

        for i in range(5):

            if self.detect():           # success enter
                self._data.currentState = self.getName()
                return True

            if MatchUtil.Having(self._device, self._enterBtnImage):
                for j in range(10):
                    if MatchUtil.TapImage(self._device, self._enterBtnImage):
                        break
                    time.sleep(1)
                
                if self.detect():           # success enter
                    self._data.currentState = self.getName()
                    return True
                
            # 往下滑
            self._device.swipe(1000, 500, 1000, 200)

        # 進入失敗
        return False

    def detect(self):
        
        if not MatchUtil.HavinginRange(self._device, Asset.BackToLobbyBtnImage, 0, 0, 228, 122):
            Logger.trace('Not having 管制室 button')
            return False
        
        return True


    def getParentName(self):
        return 'Lobby'
