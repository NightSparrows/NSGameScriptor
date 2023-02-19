


class State:

    def __init__(self, name: str) -> None:
        self.m_name = name
        pass

    def goback(self):
        raise NotImplementedError('state goback() not impl.')

    def enter(self):
        raise NotImplementedError('state goback() not impl.')

    def detect(self):
        raise NotImplementedError('state detect() not impl.')

    def getParentName(self):
        raise NotImplementedError('state getParentName() not impl.')


    def getName(self):
        return self.m_name
