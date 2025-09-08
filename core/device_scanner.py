# core/device_scanner.py
import time, threading
import serial, serial.tools.list_ports

APP_TAG = "<UDC app>"
PONG_PREFIX = "PONG RFBOX"

class DeviceScanner:
    """
    Used by MainWindow:
      - scan_async()
      - best_port attribute
    Publishes:
      - 'scan:result' -> {ports: [..], best: 'COMx'|None}
      - 'log:line'    -> '<UDC app> ...'
    """
    def __init__(self, bus, serial_cfg: dict):
        self.bus = bus
        self.cfg = serial_cfg
        self.best_port: str | None = None
        self._thread: threading.Thread | None = None

    def _log(self, msg: str):
        self.bus.publish("log:line", f"{APP_TAG} {msg}")

    def scan_async(self):
        if self._thread and self._thread.is_alive():
            self._log("Scan already running.")
            return
        self._thread = threading.Thread(target=self._scan, daemon=True)
        self._thread.start()

    # ---- internals ----
    def _scan(self):
        baud = int(self.cfg.get("baudrate", 9600))
        scan_timeout = int(self.cfg.get("scan_timeout_ms", 1500)) / 1000.0
        eol = self.cfg.get("eol", "\n")

        ports = list(serial.tools.list_ports.comports())

        # reorder: COM6 first if present
        ports.sort(key=lambda p: (0 if str(p.device).upper() == "COM6" else 1, str(p.device)))

        found_banner = None
        selected = None

        if not ports:
            self._log("No serial ports found.")
            self.bus.publish("scan:result", {"ports": [], "best": None})
            return

        self._log(f"Found {len(ports)} port(s). Probing with PING…")
        for p in ports:
            desc = getattr(p, "description", "")
            loc  = getattr(p, "location", "")
            hwid = getattr(p, "hwid", "")
            self._log(f"Probing {p.device} | desc='{desc}' loc='{loc}' hwid='{hwid}'")
            try:
                s = serial.Serial(
                    port=p.device,
                    baudrate=baud,
                    timeout=0.35,
                    write_timeout=0.35,
                )
                # let board settle; then clear banner
                time.sleep(2.0)
                s.reset_input_buffer(); s.reset_output_buffer()

                # send PING
                s.write(f"PING scan{eol}".encode("utf-8"))
                s.flush()

                t0 = time.time()
                while time.time() - t0 < scan_timeout:
                    raw = s.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line.startswith(PONG_PREFIX):
                        selected = p.device
                        found_banner = line
                        self._log(f"Selected {selected} — {found_banner}")
                        break
            except Exception as e:
                self._log(f"Open/Probe failed on {p.device}: {e}")
            finally:
                try:
                    s.close()
                except Exception:
                    pass

            if selected:
                break

        self.best_port = selected
        self.bus.publish("scan:result", {
            "ports": [pp.device for pp in ports],
            "best": selected
        })
