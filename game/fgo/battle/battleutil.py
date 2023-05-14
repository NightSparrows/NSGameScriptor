
from core.logger import Logger

from .battledata import BattleData
from .skillbattletask import SkillBattleTask
from .cardbattletask import CardBattleTask
from .jumpbattletask import JumpBattleTask
from .masterskillbattletask import MasterSkillBattleTask

class BattleUtil:

    # state method for searialize the battle script
    def SerializeTask(data: BattleData, script: str):
        tasks = list()

        scriptLines = script.splitlines()

        for line in scriptLines:
            cmdArgs = line.split(' ')
            if cmdArgs[0] == 'skill':
                task = None
                if len(cmdArgs) == 3:
                    task = SkillBattleTask(data, charNo=int(cmdArgs[1]), skillNo=int(cmdArgs[2]), useCharNo=-1)
                elif len(cmdArgs) == 4:
                    task = SkillBattleTask(data, charNo=int(cmdArgs[1]), skillNo=int(cmdArgs[2]), useCharNo=int(cmdArgs[3]))
                else:
                    Logger.error('skill command syntax error')
                    return None
                tasks.append(task)
            elif cmdArgs[0] == 'card':
                assert(len(cmdArgs) == 4)
                task = CardBattleTask(data, [cmdArgs[1], cmdArgs[2], cmdArgs[3]])
                tasks.append(task)
            elif cmdArgs[0] == 'ms':
                if len(cmdArgs) == 2:
                    task = MasterSkillBattleTask(data, int(cmdArgs[1]), -1)
                elif len(cmdArgs) == 3:
                    task = MasterSkillBattleTask(data, int(cmdArgs[1]), int(cmdArgs[2]))
                else:
                    Logger.error('skill command syntax error')
                    return None
                tasks.append(task)
            elif cmdArgs[0] == 'jump':
                assert(len(cmdArgs) >= 2)
                task = JumpBattleTask(data, int(cmdArgs[1]))
                tasks.append(task)
                Logger.trace('jump cmd append.')
            else:
                Logger.error("Unknown script command.")

        return tasks
