# Ping–Pong scanning
import serial, serial.tools.list_ports, time, threading

class DeviceScanner:
    def __init__(self, bus, serial_cfg):
        self.bus = bus
        self.cfg = serial_cfg
        self.best_port = None

    def scan_async(self):
        threading.Thread(target=self._scan, daemon=True).start()

    def _scan(self):
        ports = serial.tools.list_ports.comports()
        ping = (self.cfg["ping"] + self.cfg["eol"]).encode()
        timeout = self.cfg.get("scan_timeout_ms", 800)/1000.0
        best = None
        for p in ports:
            if "Bluetooth" in (p.description or ""): continue
            try:
                ser = serial.Serial(p.device, self.cfg["baudrate"], timeout=timeout)
                time.sleep(0.15)
                ser.reset_input_buffer(); ser.reset_output_buffer()
                ser.write(ping)
                time.sleep(0.3)
                resp = ser.read(128).decode(errors="ignore")
                ser.close()
                if self.cfg["pong"] in resp:
                    best = p.device
                    break
            except Exception:
                pass
        self.best_port = best
        self.bus.publish("scan:result", {"best": best})
