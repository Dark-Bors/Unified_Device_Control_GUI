# Thread-safe pub/sub
import queue, threading

class EventBus:
    def __init__(self):
        self.q = queue.Queue()
        self.handlers = {}
        self._pump_started = False

    def publish(self, topic, payload):
        if isinstance(payload, str):
            payload = payload  # allow direct strings for log lines
        self.q.put((topic, payload))
        self._start_pump()

    def subscribe(self, topic, handler):
        self.handlers.setdefault(topic, []).append(handler)
        self._start_pump()

    def _start_pump(self):
        if self._pump_started: return
        self._pump_started = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while True:
            topic, payload = self.q.get()
            for h in self.handlers.get(topic, []):
                try: h(payload)
                except Exception: pass
