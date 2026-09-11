
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from core.util.cancellation import CancelledException


class WorkerSignals(QObject):
    started = Signal()
    result = Signal(object)
    error = Signal(str)
    cancelled = Signal()
    finished = Signal()


class Worker(QRunnable):
    """Wraps a blocking callable so it can run on a background thread."""

    def __init__(self, fn, *args, **kwargs) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        self.signals.started.emit()
        try:
            result = self._fn(*self._args, **self._kwargs)
        except CancelledException:
            # a deliberate Device.requestCancel() (e.g. the GUI's 停止
            # button), not a real failure - kept separate from `error` so
            # callers don't have to show a critical-error dialog for it.
            self.signals.cancelled.emit()
        except Exception as e:
            self.signals.error.emit(str(e))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class WorkerPool:
    """
    Single-threaded QThreadPool, keyed by name so different kinds of work
    don't queue behind each other.

    There are two pools in practice:
    - 'automation' (the default): task execution, battle test-runs, device
      connect/restart. These are long-running and must never run
      concurrently with each other, so this pool stays maxThreadCount=1.
      Views also read this pool's isBusy() to disable Run/Execute buttons.
    - 'screenshot': live screen preview captures. This is its own pool so
      watching the live screen keeps working while a task/battle is
      running on the 'automation' pool instead of silently stalling behind
      it for the run's whole duration. adb/NemuIPC screenshot reads are
      safe to issue concurrently with other adb commands on the same
      device, so running them on a separate thread is safe.
    """

    _instances = {}

    def __init__(self, maxThreads: int = 1) -> None:
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(maxThreads)
        # Qt takes C++-side ownership of a started QRunnable (autoDelete)
        # and nothing else holds a Python reference to Worker/WorkerSignals
        # once submit() returns, so without this the worker (and its
        # signals) can be garbage-collected mid-flight - in practice this
        # dropped the 'finished' signal after 'result' had already fired.
        # Keeping a strong reference here until 'finished' is delivered
        # prevents that race.
        self._active = set()

    @classmethod
    def instance(cls, name: str = 'automation') -> 'WorkerPool':
        if name not in cls._instances:
            cls._instances[name] = WorkerPool()
        return cls._instances[name]

    def isBusy(self) -> bool:
        return self._pool.activeThreadCount() > 0

    def submit(self, fn, *args, on_result=None, on_error=None, on_cancelled=None, on_finished=None, on_started=None, **kwargs) -> Worker:
        worker = Worker(fn, *args, **kwargs)
        self._active.add(worker)

        if on_result is not None:
            worker.signals.result.connect(on_result)
        if on_error is not None:
            worker.signals.error.connect(on_error)
        if on_cancelled is not None:
            worker.signals.cancelled.connect(on_cancelled)
        if on_started is not None:
            worker.signals.started.connect(on_started)

        worker.signals.finished.connect(lambda: self._active.discard(worker))
        if on_finished is not None:
            worker.signals.finished.connect(on_finished)

        self._pool.start(worker)
        return worker
