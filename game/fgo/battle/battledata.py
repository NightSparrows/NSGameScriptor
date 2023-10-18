
import numpy


from core.device.device import Device

class BattleData:
    executePC = 0              # the execution program counter
    device: Device
    appleType: str
    _thugImage: numpy.ndarray
