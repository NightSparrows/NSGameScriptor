

import datetime

from core.logger import Logger

from .task import Task

class TaskManager:

    

    def __init__(self) -> None:
        self._tasks = []

    def addTask(self, task: Task):
        self._tasks.append(task)

    # return
    # -1: 非法ID
    # -2: 執行失敗
    def runTask(self, id: int):
        if id < 0 or id >= len(self._tasks):
            return -1

        task = self._tasks[id]
        result = task.execute()

        if not result:
            Logger.error('工作[' + task.getInfo() + ']執行失敗')
            return -2

        Logger.info('工作[' + task.getInfo() + ']執行成功')
        return 0



    # 執行已過期的工作
    def execute(self):

        Logger.trace('執行未使用的工作')

        taskQueue = []

        currentTime = datetime.datetime.now()

        for task in self._tasks:
            if task.getDate() < currentTime and task.isEnable():
                Logger.trace('工作[' + task.getName()+'] 已過期')
                taskQueue.append(task)
            
        
        sorted(taskQueue, key=lambda x: x.getDate())

        Logger.info('Have ' + str(len(taskQueue)) + ' tasks to run')
        for task in taskQueue:
            Logger.info('Executing ' + task.getInfo())
            if task.execute():
                Logger.info('工作[' + task.getInfo() + ']執行成功')
            else:
                Logger.error('工作[' + task.getInfo() + ']執行失敗')
        






