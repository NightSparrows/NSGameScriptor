
import time

class Timer:

    def __init__(self, timeout: float) -> None:
        self.m_timeout = timeout
        self.m_time = 0

    def restart(self):
        self.m_lastTime = time.time()
        self.m_time = 0
    
    def timeout(self) -> bool:

        currentTime = time.time()
        elaspedTime = currentTime - self.m_lastTime
        self.m_lastTime = currentTime

        self.m_time += elaspedTime

        return self.m_time >= self.m_timeout

