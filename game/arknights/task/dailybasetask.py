
import cv2
import datetime
import time

from core.logger import Logger
from core.game.statemanager import StateManager
from core.game.task import Task

from core.matchutil import MatchUtil

class DailyBaseTask(Task):

    def __init__(self, stateManager: StateManager, game, date: datetime, enable: bool = True) -> None:
        super().__init__('DailyBaseTask', date, enable)
        self._stateManager = stateManager
        self._game = game
        self._device = game._device
        self._notifIcon = cv2.imread('assets/arknights/task/dailybasetask/notification.png')
        self._orderBtn = cv2.imread('assets/arknights/task/dailybasetask/orderBtn.png')
        self._takenBtn = cv2.imread('assets/arknights/task/dailybasetask/takenBtn.png')
        self._tradeIcon = cv2.imread('assets/arknights/task/dailybasetask/tradeIcon.png')
        self._manuIcon = cv2.imread('assets/arknights/task/dailybasetask/manuIcon.png')

    def execute(self):

        if not self._stateManager.goto('Base'):
            return False

        # 案notification 成功
        if MatchUtil.TapImage(self._device, self._notifIcon, 0.95):
            Logger.info('Has notification button')

            isOrder = False
            isTaken = False

            while not (isOrder and isTaken):
                if MatchUtil.TapImage(self._device, self._orderBtn, 0.95):
                    isOrder = True

                if MatchUtil.TapImage(self._device, self._takenBtn, 0.95):
                    isTaken = True
                
                # TODO 倒數計時的function
            
            # 案回
            self._device.tap(410, 180)
            time.sleep(1)
            

        Logger.info('zoom out ... ')
        self._device.zoomOut(1)
        time.sleep(1)

        # trade harvest
        Logger.info('Harvesting 貿易站')
        self._device.screenshot()
        image = self._device.getScreenshot()

        cv2.imshow('', image)
        cv2.waitKey(0)

        tradeResult = MatchUtil.match(image, self._tradeIcon)

        while MatchUtil.isMatch(tradeResult):
            point = MatchUtil.calculated(tradeResult, self._tradeIcon.shape)

            self._device.tap(point['x']['center'] - 60, point['y']['center'] + 20)
            time.sleep(1)
                
            self._device.screenshot()
            image = self._device.getScreenshot()

            tradeResult = MatchUtil.match(image, self._tradeIcon)
        
        # end trade harvest

        # manufactor harvest 
        Logger.info('Harvesting 製造站')
        self._device.screenshot()
        image = self._device.getScreenshot()

        result = MatchUtil.match(image, self._tradeIcon)

        while MatchUtil.isMatch(result):
            Logger.info('harvesting ...')
            point = MatchUtil.calculated(result, self._manuIcon.shape)

            self._device.tap(point['x']['center'] - 30, point['y']['center'] + 20)
            time.sleep(1)
                
            self._device.screenshot()
            image = self._device.getScreenshot()

            result = MatchUtil.match(image, self._manuIcon)
        
        # end manufactor harvest

            

            
            





        #raise NotImplementedError()
    
        return True
