
from ...core.game.game import Game

from ...core.device.device import Device

class GameBlueArchive(Game):

    def __init__(self, device: Device) -> None:
        super().__init__('BlueArchive')
        self._device = device
    
    def execute(self):


        raise NotImplementedError('Game ' + self.m_name + ' execute not impl')

    def restart(self):

        self._device.killApp('com.nexon.bluearchive')
        self._device.openApp('com.nexon.bluearchive/.MxUnityPlayerActivity')


        # TODO 進入大廳

        raise NotImplementedError('Game ' + self.m_name + ' restart not impl.')
