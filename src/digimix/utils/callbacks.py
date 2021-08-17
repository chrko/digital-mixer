import threading


class CallbackBase:
    def __init__(self):
        self._callbacks = []
        self._callback_lock = threading.RLock()

    def add_callback(self, func):
        with self._callback_lock:
            self._callbacks.append(func)

    def remove_callback(self, func):
        with self._callback_lock:
            self._callbacks.remove(func)

    def clear_callbacks(self):
        with self._callback_lock:
            self._callbacks.clear()
