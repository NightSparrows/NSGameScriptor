
import cv2
from enum import Enum
import time

from core.logger import Logger
from core.device.device import Device
from core.matchutil import MatchUtil
from core.util.timer import Timer

from game.fgo.asset import Asset

from .battledata import BattleData
from .battleutil import BattleUtil
from .apple import Apple

class Battle:

    class Stage(Enum):
        ChooseFriend = 'chooseFriend'
        ChooseParty = 'chooseParty'
        InBattle = 'inBattle'
        End = 'end'

    s_inBattleFlagImage = cv2.imread('.//assets//fgo//battle//inBattleFlag.png')
    s_touchImage = cv2.imread('.//assets//fgo//battle//touch.png')
    s_attackBtnImage = cv2.imread('.//assets//fgo//battle//attackBtn.png')
    
    s_winConditionImage = cv2.imread('.//assets//fgo//battle//winCondition.png')
    s_nextStepBtnImage = cv2.imread('.//assets//fgo//battle//nextStepBtn.png')
    s_endDicisionImage = cv2.imread('.//assets//fgo//battle//endDicision.png')
    s_refreshBtnImage = cv2.imread('.//assets//fgo//battle//refreshBtn.png')
    s_friendConfirmImage = cv2.imread('.//assets//fgo//battle//friendConfirm.png')
    s_missionStartBtnImage = cv2.imread('./assets/fgo/battle/missionStartBtn.png')

    # friendInfo= {
            # 'name' : friend,
            # 'class' : 5,            # TODO: 我懶得設定以後再說，預設術職
            # 'nameImage' : cv2.imread('.//assets//fgo//servant//' + friend + '//name.png'),
            # 'skill1' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill1.png'),
            # 'skill2' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill2.png'),
            # 'skill3' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill3.png')
            # }
    def __init__(self, device: Device, partyNumber: int, friendInfo, skill, script: str) -> None:
        self._partyNumber = partyNumber
        self._friendInfo = friendInfo
        self._skill = skill
        self._script = script               # for serialization

        # serialize script
        self._data = BattleData()
        self._data.device = device
        self._tasks = BattleUtil.SerializeTask(self._data, script)
        Logger.info('Implement ' + str(len(self._tasks)) + ' tasks.')

        self._skipChooseParty = False


    # 選擇好友的method
    def chooseFriend(self):
        inStage = False
        Logger.info('assert is in choose friend stage')
        for i in range(3):      # retry 3 time for checking it is in choose friend stage
            time.sleep(1)
            self._data.device.screenshot()
            result = MatchUtil.match(self._data.device.getScreenshot(), Asset.chooseFriendIcon)
            if MatchUtil.isMatch(result):
                inStage = True
                break
        
        if not inStage:
            return False
        
        # 選擇助戰職階
        classX = 90 + self._friendInfo['class'] * 68
        Logger.info('choosing the correct classes ... ')
        self._data.device.tap(classX, 128)
        time.sleep(1)

        # Find servant
        foundServant = False
        Logger.info('Finding servant ... ')
        refreshCount = 0
        while True:
            for i in range(10):
                # scan for servant
                foundServant = False
                time.sleep(1)
                self._data.device.screenshot()
                result = MatchUtil.match(self._data.device.getScreenshot(), self._friendInfo['nameImage'])
                if MatchUtil.isMatch(result):                        # found servant
                    Logger.info('Found servant!')
                    foundServant = True
                    # check the skill 
                    servantPosition = [result['max_loc'][0], result['max_loc'][1]]
                    skillLeft = servantPosition[0] + 460
                    skillTop = servantPosition[1]
                    skillImage = self._data.device.getScreenshot()[skillTop:(skillTop + 105), skillLeft:(skillLeft + 300)]
                    #cv2.imshow('', skillImage)
                    #cv2.waitKey(0)


                    if (self._skill[0] == True):
                        Logger.info('Checking skill 1 ... ')
                        try:
                            result = MatchUtil.match(skillImage, self._friendInfo['skill1'])
                            if (not MatchUtil.isMatch(result)):
                                foundServant = False
                            else:
                                Logger.info('Skill 1 match!')
                        except:
                            foundServant = False
                    if (self._skill[1] == True):
                        Logger.info('Checking skill 2 ... ')
                        try:
                            result = MatchUtil.match(skillImage, self._friendInfo['skill2'])
                            if (not MatchUtil.isMatch(result)):
                                foundServant = False    # 不符合找下一個
                            else:
                                Logger.info('Skill 2 match!')
                        except:
                            foundServant = False
                    if (self._skill[2] == True):
                        Logger.info('Checking skill 3 ... ')
                        try:
                            result = MatchUtil.match(skillImage, self._friendInfo['skill3'])
                            if (not MatchUtil.isMatch(result)):
                                foundServant = False    # 不符合找下一個
                            else:
                                Logger.info('Skill 3 match!')
                        except:
                            foundServant = False
                    # TODO 禮裝檢查

                    # Choose it!
                    if (foundServant):
                        Logger.info('Servant ' + self._friendInfo['name'] + ' Found!')
                        self._data.device.tap(servantPosition[0], servantPosition[1])
                        time.sleep(1)
                        return True

                # 沒找到，scroll一個
                self._data.device.holdScroll(128, 610, 128, 450, 500)
                time.sleep(1)
            
            # 沒找到，refresh
            _, result = MatchUtil.WaitFor(self._data.device, Battle.s_refreshBtnImage, 3)
            if result == None:
                return False
            else:
                refreshCount += 1
                point = MatchUtil.calculated(result, Battle.s_refreshBtnImage.shape)
                self._data.device.tap(point['x']['center'], point['y']['center'])

                # TODO OK button press, 他是'是'
                _, result = MatchUtil.WaitFor(self._data.device, Asset.YesBtnImage, 3)
                time.sleep(1)
                if result != None:
                    point = MatchUtil.calculated(result, Asset.YesBtnImage.shape)
                    self._data.device.tap(point['x']['center'], point['y']['center'])
                    Logger.info('click ok button')
                    time.sleep(1) 
                else:
                    Logger.error('Press refresh dont have window.')
                    return False       
                if (refreshCount >= 5):
                    Logger.error('Do you dont have friends?')
                    return False
            

        return False

    def chooseParty(self):

        Logger.info('Choosing party ... ')
        # TODO Make sure you are in choose party
        time.sleep(2)
        self._data.device.tap(527, 50)
        time.sleep(1)
        
        
        partyBtnX = 527 + (self._partyNumber - 1) * 25

        time.sleep(1)
        self._data.device.tap(partyBtnX, 50)
        time.sleep(1)

        # 按任務開始
        isPressed = False
        for i in range(5):
            if MatchUtil.TapImage(self._data.device, Battle.s_missionStartBtnImage):
                isPressed = True
                break
            time.sleep(1)
        
        if not isPressed:
            Logger.error('Failed to press mission start button')
            return False

        return True


    def inBattle(self):

        # init battle variables
        self._data.executePC = 0
        
        _, result = MatchUtil.WaitFor(self._data.device, Battle.s_inBattleFlagImage, 60)
        _, result = MatchUtil.WaitFor(self._data.device, Battle.s_attackBtnImage, 60)

        isWin = False
        while not isWin:

            Logger.info('Wait for battle safty stage...')
            timer = 0
            while timer < 60.0:
                self._data.device.screenshot()
                screenshot = self._data.device.getScreenshot()
                result1 = MatchUtil.match(screenshot, Battle.s_inBattleFlagImage)
                result2 = MatchUtil.match(screenshot, Battle.s_attackBtnImage)
                if (MatchUtil.isMatch(result1) and MatchUtil.isMatch(result2)):
                    break       # is safty
                #check win condition
                result = MatchUtil.match(screenshot, Battle.s_nextStepBtnImage)
                if MatchUtil.isMatch(result):
                    isWin = True
                    break
                self._data.device.tap(900, 55)
                time.sleep(1)
                timer += 1

            # assert in stable battle state
            time.sleep(1)
            if isWin:
                break

            if (timer >= 60):
                Logger.error('Failed to wait safty stage')
                return False

            if (self._data.executePC == len(self._tasks)):
                # check if it is 
                _, result = MatchUtil.WaitFor(self._data.device, Battle.s_touchImage, 5)
                if (result != None):
                    self._data.device.tap(640, 360)
                    isWin = True
                    break
                else:
                    Logger.error('Your script is at the end, but the battle is not end!')
                    return False

            self._tasks[self._data.executePC].execute()
            self._data.executePC += 1
        
        if isWin:
            Logger.info('Battle win')
            self._data.device.tap(1100, 640)
            time.sleep(1)
            return True
            # tap the next step btn ...
        raise NotImplementedError()

    def execute(self, count: int = 1):

        self._currentStage = Battle.Stage.ChooseFriend
        self._skipChooseParty = False
        self._endFlags = False

        executeCount = 0

        while not self._endFlags:
            if self._currentStage == Battle.Stage.ChooseFriend:
                if not self.chooseFriend():
                    Logger.error('Failed to choose friend!')
                    return False, executeCount
                else:
                    Logger.trace('Choosing friend successfully')
                    if self._skipChooseParty:
                        self._currentStage = Battle.Stage.InBattle
                    else:
                        self._currentStage = Battle.Stage.ChooseParty
            elif self._currentStage == Battle.Stage.ChooseParty:
                Logger.trace('Entering choose party state')
                if not self.chooseParty():
                    Logger.error('Failed to choose party')
                else:
                    self._currentStage = Battle.Stage.InBattle
            elif self._currentStage == Battle.Stage.InBattle:
                Logger.trace('Entering in battle state')
                if not self.inBattle():
                    Logger.error('Failed to do battle')
                else:
                    self._currentStage = Battle.Stage.End
            elif self._currentStage == Battle.Stage.End:  # 戰鬥結束
                executeCount += 1

                timer = Timer(5)

                havingDisionWindow = False
                while not timer.timeout():
                    if MatchUtil.Having(self._data.device, Battle.s_nextStepBtnImage):
                        Logger.info('Encounter 下一步')
                        self._data.device.tap(1110, 647)
                        timer.restart()
                    elif MatchUtil.Having(self._data.device, Battle.s_friendConfirmImage):
                        Logger.info('Encounter 好友視窗')
                        Logger.info('好友申請，直接拒絕')
                        self._data.device.tap(329, 616)
                        timer.restart()
                    elif MatchUtil.Having(self._data.device, Battle.s_endDicisionImage):
                        Logger.info('Encounter 重複刷關的視窗')
                        havingDisionWindow = True
                        if (executeCount == count):
                            Logger.info('刷完了，點離開')
                            self._endFlags = True
                            self._data.device.tap(444, 567)
                            time.sleep(1)
                        else:
                            self._skipChooseParty = True
                            self._data.device.tap(840, 565)
                            time.sleep(1)

                            # checking apple
                            Apple.checkAppleWindow(self._data.device)
                            self._currentStage = Battle.Stage.ChooseFriend
                        break

                if not havingDisionWindow:
                    Logger.error('無法找到結束確認視窗')
                    return False, executeCount

                # Logger.info('確認活動視窗')
                # while True:
                #     result, _ = MatchUtil.WaitFor(self._data.device, Battle.s_nextStepBtnImage, 2)
                #     if not result:
                #         break
                #     else:
                #         self._data.device.tap(1110, 647)
                #         time.sleep(1)
                
                # # TODO 好友申請
                # time.sleep(1)
                # Logger.info('確認好友申請')
                # result, _ = MatchUtil.WaitFor(self._data.device, Battle.s_friendConfirmImage, 2)
                # if result:
                #     #直接拒絕
                #     Logger.info('好友申請，直接拒絕')
                #     self._data.device.tap(329, 616)
                #     time.sleep(1)

                # Logger.info('戰鬥結束，完成第' + str(executeCount) + '次')
                # _, result = MatchUtil.WaitFor(self._data.device, Battle.s_endDicisionImage, 5)
                # time.sleep(1)

                

                # if result == None:
                #     Logger.error('無法找到結束確認視窗')
                #     return False, executeCount
                # else:
                #     if (executeCount == count):
                #         self._endFlags = True
                #         self._data.device.tap(444, 567)
                #         time.sleep(1)
                #     else:
                #         self._skipChooseParty = True
                #         self._data.device.tap(840, 565)
                #         time.sleep(1)

                #         # checking apple
                #         Apple.checkAppleWindow(self._data.device)
                #         self._currentStage = Battle.Stage.ChooseFriend

            else:
                Logger.error('Unknown battle stage')
                return False, executeCount
        
        Logger.info('Battle task complete.')
        return True, executeCount
        


