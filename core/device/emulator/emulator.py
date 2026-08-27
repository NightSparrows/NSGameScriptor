
class Emulator:
    """Abstract emulator process lifecycle - open/close/status. Mirrors
    core/device/screencap/screencap.py's ScreenCap abstraction: a base
    class with concrete per-emulator implementations selected by Device."""

    def isRunning(self) -> bool:
        raise NotImplementedError()

    def launch(self) -> bool:
        raise NotImplementedError()

    def shutdown(self) -> bool:
        raise NotImplementedError()

    # if not already running, launch() then poll until it is (or timeout)
    def waitUntilReady(self, timeout: float = 90) -> bool:
        raise NotImplementedError()
