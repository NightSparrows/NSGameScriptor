

from .task import Task

class TaskManager:

    

    def __init__(self) -> None:
        self._tasks = []

    def addTask(self, task: Task):
        self._tasks.append(task)
