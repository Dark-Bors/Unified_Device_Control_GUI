# Handles serial comms
import serial, threading, time

class SerialManager:
    def __init__(self, bus, baud=115200, eol="\n"):
        self.bus = bus
        self.baud = baud
        self.eol = eol
        self.port = None
        self.ser = None
        self.stop = threading.Event()
        self.reader = None

    def open(self, port):
        if not port: return False
        try:
            self.ser = serial.Serial(port, self.baud, timeout=0.1)
            self.port = port
            self.stop.clear()
            self.reader = threading.Thread(target=self._read_loop, daemon=True)
            self.reader.start()
            self.bus.publish("conn:state", {"connected": True, "port": port})
            return True
        except Exception:
            self.close()
            return False

    def close(self):
        self.stop.set()
        if self.ser:
            try: self.ser.close()
            except: pass
        self.ser = None
        self.bus.publish("conn:state", {"connected": False})

    def write_line(self, text: str):
        if not self.ser or not self.ser.is_open: return False
        try:
            self.ser.write((text + self.eol).encode())
            return True
        except Exception:
            return False

    def _read_loop(self):
        buf = b""
        while not self.stop.is_set():
            try:
                chunk = self.ser.read(256)
                if chunk:
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        s = line.decode(errors="ignore").strip()
                        if s:
                            self.bus.publish("log:line", s)
                else:
                    time.sleep(0.02)
            except Exception:
                break
