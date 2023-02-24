

import datetime

from core.logger import Logger

from .task import Task

class TaskManager:

    

    def __init__(self) -> None:
        self._tasks = []

    def addTask(self, task: Task):
        self._tasks.append(task)

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

        for task in taskQueue:
            # TODO 標記未正確執行的工作
            task.execute()
        






