


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

    # None means this is a root state (no parent to navigate back to).
    # Only override this for non-root states.
    def getParentName(self):
        return None


    def getName(self):
        return self.m_name
