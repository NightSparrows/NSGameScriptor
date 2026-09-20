
import os
import cv2
from datetime import datetime
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
    s_continueBtnImage = cv2.imread('.//assets//fgo//battle//continueBtn.png')
    s_refreshBtnImage = cv2.imread('.//assets//fgo//battle//refreshBtn.png')
    s_refreshBtn2Image = cv2.imread('./assets/fgo/battle/refreshBtn2.png')       # 新版 UI (文字單行)
    s_closeBtnImage = cv2.imread('.//assets//fgo//battle//closeBtn.png')
    s_friendConfirmImage = cv2.imread('.//assets//fgo//battle//friendConfirm.png')
    s_missionStartBtnImage = cv2.imread('./assets/fgo/battle/missionStartBtn.png')
    s_missionStartBtn2Image = cv2.imread('./assets/fgo/battle/missionStartBtn2.png')
    s_chooseFriendSkillSwitchBtn = cv2.imread('./assets/fgo/battle/chooseFriendSkillSwitchBtn.png')

    # friendInfo= {
            # 'name' : friend,
            # 'class' : 5,            # TODO: 我懶得設定以後再說，預設術職
            # 'nameImage' : cv2.imread('.//assets//fgo//servant//' + friend + '//name.png'),
            # 'skill1' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill1.png'),
            # 'skill2' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill2.png'),
            # 'skill3' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill3.png')
            # }
    # craftEssenceNo: 禮裝No
    def __init__(self, device: Device, name: str, partyNumber: int, friendInfo, skill, script: str, craftEssenceNo: int = -1) -> None:
        self._name = name
        self._partyNumber = partyNumber
        self._friendInfo = friendInfo
        self._skill = skill
        self._script = script               # for serialization

        # serialize script
        self._data = BattleData()

        thugImageFilePath = './settings/fgo/battle/' + self._name + '/thugImage.png'
        if os.path.exists(thugImageFilePath):
            self._data._thugImage = cv2.imread(thugImageFilePath)
        else:
            Logger.warn('Warning: This script[' + self._name + '] dont have thugImage.png script maybe run error') 
        self._data.device = device
        self._tasks = BattleUtil.SerializeTask(self._data, script)
        Logger.info('Implement ' + str(len(self._tasks)) + ' tasks.')

        self._skipChooseParty = False

        self._craftEssenceNo = craftEssenceNo
        if craftEssenceNo != -1:
            self._craftEssenceImg = cv2.imread('./assets/fgo/craftEssence/' + str(craftEssenceNo) + '.png')
            self._haveCraftEssence = True
        else:
            self._haveCraftEssence = False


    # 助戰清單的區域 (不含上方職階列, 右邊捲軸也算進去, 捲動時它會跟著動)
    s_friendListRegion = (170, 720, 0, 1280)

    # 兩張截圖的助戰清單是否不同 (清單捲到底/頂時捲動不會讓畫面改變)
    def _friendListChanged(before, after) -> bool:
        top, bottom, left, right = Battle.s_friendListRegion
        diff = cv2.absdiff(before[top:bottom, left:right], after[top:bottom, left:right])
        return float(diff.mean()) > 0.5

    # 把助戰清單往上捲到頂, 捲到畫面不再變化為止
    def _scrollFriendListToTop(self, maxScroll: int = 15):
        device = self._data.device
        device.screenshot()
        prev = device.getScreenshot()
        for _ in range(maxScroll):
            device.holdScroll(128, 450, 128, 610, 500)
            device.sleep(1)
            device.screenshot()
            cur = device.getScreenshot()
            if not Battle._friendListChanged(prev, cur):
                return
            prev = cur

    # 比對助戰從者的技能圖示, 會印出分數方便調整門檻
    def _matchFriendSkill(self, skillImage, skillIndex: int, thresh: float) -> bool:
        Logger.info('Checking skill ' + str(skillIndex) + ' ... ')
        try:
            result = MatchUtil.match(skillImage, self._friendInfo['skill' + str(skillIndex)])
        except Exception as e:
            Logger.warn('Skill ' + str(skillIndex) + ' check error: ' + str(e))
            return False
        score = result['max_val']
        if MatchUtil.isMatch(result, thresh):
            Logger.info('Skill ' + str(skillIndex) + ' match! (' + format(score, '.3f') + ')')
            return True
        Logger.info('Skill ' + str(skillIndex) + ' not match (' + format(score, '.3f') + ' < ' + str(thresh) + ')')
        return False

    # 選擇好友的method
    def chooseFriend(self):
        inStage = False
        Logger.info('assert is in choose friend stage')
        for i in range(3):      # retry 3 time for checking it is in choose friend stage
            self._data.device.sleep(1)
            self._data.device.screenshot()
            result = MatchUtil.match(self._data.device.getScreenshot(), Battle.s_chooseFriendSkillSwitchBtn)
            if MatchUtil.isMatch(result):
                inStage = True
                break
        
        if not inStage:
            return False
        
        # 選擇助戰職階
        classX = 90 + self._friendInfo['class'] * 68
        Logger.info('choosing the correct classes ... ')
        self._data.device.tap(classX, 128)
        self._data.device.sleep(1)

        # Find servant
        foundServant = False
        Logger.info('Finding servant ... ')
        refreshCount = 0
        # 點職階頁籤不一定會讓清單回到頂端, 先自己捲回去再開始找
        self._scrollFriendListToTop()
        while True:
            prevScreenshot = None
            for i in range(10):
                # scan for servant
                foundServant = False
                self._data.device.sleep(1)
                self._data.device.screenshot()
                screenshot = self._data.device.getScreenshot()

                # 捲動後畫面沒變 = 清單已經到底, 不用再空捲, 直接去更新
                if prevScreenshot is not None and not Battle._friendListChanged(prevScreenshot, screenshot):
                    Logger.info('Reach the end of friend list')
                    break
                prevScreenshot = screenshot

                #result = MatchUtil.match(self._data.device.getScreenshot(), self._friendInfo['nameImage'])
                matchResults = MatchUtil.matchMultiple(screenshot, self._friendInfo['nameImage'])

                for servantPosition in matchResults:
                #if MatchUtil.isMatch(result):                        # found servant
                    Logger.info('Found servant!')
                    foundServant = True
                    # check the skill 
                    #servantPosition = [result['max_loc'][0], result['max_loc'][1]]
                    skillLeft = servantPosition[0] + 460
                    skillTop = servantPosition[1]
                    skillImage = screenshot[skillTop:(skillTop + 105), skillLeft:(skillLeft + 150)]
                    #cv2.imshow('', skillImage)
                    #cv2.waitKey(0)

                    for skillIndex, (needCheck, thresh) in enumerate(zip(self._skill[:3], (0.8, 0.8, 0.8)), start=1):
                        if needCheck and not self._matchFriendSkill(skillImage, skillIndex, thresh):
                            foundServant = False    # 不符合找下一個
                    # TODO 禮裝檢查

                    # Choose it!
                    if (foundServant):
                        Logger.info('Servant ' + self._friendInfo['name'] + ' Found!')

                        if self._haveCraftEssence:
                            # Match 裡裝!
                            #cv2.imshow("", self._data.device.getScreenshot()[servantPosition[1]:servantPosition[1]+115, 50:210])
                            #cv2.waitKey(0)
                            if MatchUtil.HavinginRange(self._data.device, self._craftEssenceImg, 50, servantPosition[1], 160, 115, 0.95):
                                Logger.info('禮裝 match!')
                                self._data.device.tap(servantPosition[0], servantPosition[1])
                                self._data.device.sleep(1)
                                return True
                            Logger.info('禮裝 not match')
                        else:
                            self._data.device.tap(servantPosition[0], servantPosition[1])
                            self._data.device.sleep(1)
                            return True

                # 沒找到，scroll一個
                self._data.device.holdScroll(128, 610, 128, 450, 500)
                self._data.device.sleep(1)
            
            # 沒找到，refresh
            # 剛更新過會有冷卻時間 (按鈕上顯示秒數), 找不到按鈕就等一下再試
            result = False
            for _ in range(6):
                result = MatchUtil.TapAnyImage(self._data.device, (Battle.s_refreshBtn2Image, Battle.s_refreshBtnImage))
                if result:
                    break
                self._data.device.sleep(2)

            if result:
                refreshCount += 1
                self._data.device.sleep(0.5)
                if not MatchUtil.TapImage(self._data.device, Asset.YesBtnImage):
                    Logger.error('無法按下 是 按鈕')
                    return False
                
                if refreshCount == 5:
                    Logger.error('Do you dont have friends?')
                    return False

                self._scrollFriendListToTop()
            else:
                os.makedirs('./tmp', exist_ok=True)
                cv2.imwrite('./tmp/refreshBtnFail.png', self._data.device.getScreenshot())
                Logger.error('無法按列表更新按鈕 (screenshot saved to tmp/refreshBtnFail.png)')
                return False
            

        return False

    def chooseParty(self):

        Logger.info('Choosing party ... ')
        # TODO Make sure you are in choose party
        self._data.device.sleep(2)
        self._data.device.tap(465, 50)
        self._data.device.sleep(1)
        
        
        partyBtnX = 465 + (self._partyNumber - 1) * 25

        self._data.device.sleep(1)
        self._data.device.tap(partyBtnX, 50)
        self._data.device.sleep(1)

        # 按任務開始
        isPressed = False
        for i in range(5):
            self._data.device.screenshot()
            screenshot = self._data.device.getScreenshot()
            for template in (Battle.s_missionStartBtnImage, Battle.s_missionStartBtn2Image):
                result = MatchUtil.match(screenshot, template)
                Logger.info('Mission start button score: ' + format(result['max_val'], '.3f'))
                if MatchUtil.isMatch(result, 0.9):
                    point = MatchUtil.calculated(result, template.shape)
                    self._data.device.tap(point['x']['center'], point['y']['center'])
                    self._data.device.sleep(1)
                    isPressed = True
                    break
            if isPressed:
                break
            self._data.device.sleep(1)
        
        if not isPressed:
            # 留下當下的畫面, 方便確認是哪個畫面找不到按鈕
            os.makedirs('./tmp', exist_ok=True)
            cv2.imwrite('./tmp/missionStartBtnFail.png', screenshot)
            Logger.error('Failed to press mission start button (screenshot saved to tmp/missionStartBtnFail.png)')
            return False

        return True

    def waitSaftyStageInBattle(self, timer: Timer):
        '''
        Return: True: is win
                False: is safty
        '''
    
        Logger.info('Wait for battle safty stage...')
        
        timer.restart()
        while not timer.timeout():
            self._data.device.sleep(0.3)
            self._data.device.screenshot()
            screenshot = self._data.device.getScreenshot()
            result1 = MatchUtil.match(screenshot, Battle.s_inBattleFlagImage)
            #result2 = MatchUtil.match(screenshot, Battle.s_attackBtnImage)

            if MatchUtil.HavinginRange(self._data.device, Battle.s_closeBtnImage, 0, 0, 72, 60):
                Logger.info('Detect a new 禮裝')
                self._data.device.tap(45, 42)
                self._data.device.sleep(0.2)

            #check win condition
            result = MatchUtil.match(screenshot, Battle.s_nextStepBtnImage)
            if MatchUtil.isMatch(result):
                return True
            
            # if not MatchUtil.MatchColor(screenshot[573, 1130], 0, 209, 242):
            #     continue # 沒有藍色按鈕

            #if (MatchUtil.isMatch(result1, 0.8) and MatchUtil.isMatch(result2, 0.8)):
            if (MatchUtil.isMatch(result1)):
                return False

            # 點空白的地方
            self._data.device.tap(900, 55)

        pass

    # 技能列的區域 (三隻從者的技能圖示), 用來判斷戰鬥介面是不是已經穩定
    s_skillBarRegion = (540, 620, 30, 960)

    # 等戰鬥介面穩定 (技能列連續幾張截圖都沒變)
    # 剛進戰鬥時 Menu 已經出現, 但開場動畫還在跑, 這時點技能會點不到
    # 而且技能有沒有按到是用顏色有沒有變來判斷, 動畫也會讓顏色變, 會誤判成有按到
    def _waitBattleUIStable(self, timeout: float = 10, stableCount: int = 3) -> bool:
        top, bottom, left, right = Battle.s_skillBarRegion
        device = self._data.device
        prev = None
        stable = 0
        startTime = time.time()
        while time.time() - startTime < timeout:
            device.screenshot()
            cur = device.getScreenshot()[top:bottom, left:right]
            if prev is not None and float(cv2.absdiff(prev, cur).mean()) <= 0.5:
                stable += 1
                if stable >= stableCount:
                    return True
            else:
                stable = 0
            prev = cur
            device.sleep(0.3)
        Logger.warn('Battle UI is not stable after ' + str(timeout) + ' secs, continue anyway')
        return False

    def inBattle(self):

        battleStartTime = time.time()

        self._data.device.sleep(1)
        # init battle variables
        self._data.executePC = 0
        
        # for 跳過開場動畫
        #_, result = MatchUtil.WaitFor(self._data.device, Battle.s_inBattleFlagImage, 60)
        #_, result = MatchUtil.WaitFor(self._data.device, Battle.s_attackBtnImage, 60)

        isWin = False

        timer = Timer(60)

        self.waitSaftyStageInBattle(timer)

        # first time wait until the opening animation is done
        self._waitBattleUIStable()

        while not isWin:
            if self.waitSaftyStageInBattle(timer):
                isWin = True
                break

            # assert in stable battle state
            self._data.device.sleep(0.8)
            if isWin:
                break

            if (timer.timeout()):
                Logger.error('Failed to wait safty stage')
                return False


            # 確定在選擇階段

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
            battleTime = time.time() - battleStartTime
            Logger.info('Battle time: ' + str(battleTime) + 'secs')
            self._data.device.tap(1100, 640)
            self._data.device.sleep(1)
            return True
            # tap the next step btn ...
        raise NotImplementedError()

    def execute(self, count: int = 1) -> bool | int:

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
                    return False, executeCount
                else:
                    self._currentStage = Battle.Stage.InBattle
            elif self._currentStage == Battle.Stage.InBattle:
                Logger.trace('Entering in battle state')
                if not self.inBattle():
                    Logger.error('Failed to do battle')
                    return False, executeCount
                else:
                    self._currentStage = Battle.Stage.End
            elif self._currentStage == Battle.Stage.End:  # 戰鬥結束
                executeCount += 1
                Logger.info('完成第' + str(executeCount) + '次戰鬥')

                timer = Timer(10)

                havingDisionWindow = False
                timer.restart()
                while not timer.timeout():
                    if MatchUtil.Having(self._data.device, Battle.s_nextStepBtnImage):
                        Logger.info('Encounter 下一步')
                        self._data.device.tap(1110, 647)
                        self._data.device.sleep(0.5)
                        timer.restart()
                    elif MatchUtil.Having(self._data.device, Battle.s_friendConfirmImage):
                        Logger.info('Encounter 好友視窗')
                        Logger.info('好友申請，直接拒絕')
                        self._data.device.tap(329, 616)
                        self._data.device.sleep(0.5)
                        timer.restart()
                    elif MatchUtil.Having(self._data.device, Battle.s_continueBtnImage) or MatchUtil.Having(self._data.device, Battle.s_endDicisionImage):
                        Logger.info('(新) Encounter 重複刷關的視窗')
                        havingDisionWindow = True
                        if (executeCount == count):
                            Logger.info('刷完了，點離開')
                            self._endFlags = True
                            self._data.device.tap(444, 567)
                            self._data.device.sleep(1)
                        else:
                            self._skipChooseParty = True
                            self._data.device.tap(840, 565)
                            self._data.device.sleep(1)

                            # checking apple
                            Apple.checkAppleWindow(self._data.device)
                            self._currentStage = Battle.Stage.ChooseFriend
                        break
                    elif MatchUtil.HavinginRange(self._data.device, Battle.s_closeBtnImage, 0, 0, 80, 80):
                        Logger.info('Encounter 關閉按鈕')
                        self._data.device.tap(45, 40)
                        self._data.device.sleep(0.5)
                    else:
                        # 按角落
                        self._data.device.tap(1020, 5)
                        self._data.device.sleep(0.1)
                    # TODO 加入關閉功能(取得新禮裝時)

                    Logger.trace('還沒找到結束確認視窗')

                if not havingDisionWindow:
                    Logger.error('無法找到結束確認視窗')
                    return False, executeCount

            else:
                Logger.error('Unknown battle stage')
                return False, executeCount
        
        Logger.info('Battle task complete.')
        return True, executeCount
        


