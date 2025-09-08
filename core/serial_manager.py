# core/serial_manager.py
import time, threading
import serial

SERIAL_TAG = "<serial monitor>"
APP_TAG    = "<UDC app>"

class SerialManager:
    """
    Methods used by your UI:
      - open(port) -> bool
      - close()
      - write_line(cmd: str) -> bool
    State:
      - port (str|None)

    Events (bus):
      - 'conn:state' -> {connected: bool, port: str|None}
      - 'log:line'   -> str  (prefixed with <serial monitor> or <UDC app>)
    """
    def __init__(self, bus, baud=9600, eol="\n", read_timeout=0.35, write_timeout=0.35):
        self.bus = bus
        self.baud = baud
        self.eol = eol
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout

        self.ser: serial.Serial | None = None
        self.port: str | None = None

        self._stop = threading.Event()
        self._reader: threading.Thread | None = None

    # ---------- helpers ----------
    def _log_app(self, msg: str):
        self.bus.publish("log:line", f"{APP_TAG} {msg}")

    def _log_rx(self, line: str):
        self.bus.publish("log:line", f"{SERIAL_TAG} {line}")

    def _emit_conn(self, connected: bool):
        self.bus.publish("conn:state", {"connected": connected, "port": self.port})

    # ---------- public API ----------
    def open(self, port: str | None) -> bool:
        if not port:
            self._log_app("Open failed: no port specified")
            self._emit_conn(False)
            return False

        self.close()
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=self.baud,
                timeout=self.read_timeout,
                write_timeout=self.write_timeout,
            )
            # Arduino may reset on open; allow banner to finish, then clear it
            time.sleep(2.0)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            self.port = port
            self._start_reader()
            self._emit_conn(True)
            self._log_app(f"Serial monitor started on {self.port}")
            return True
        except Exception as e:
            self._log_app(f"Open failed on {port}: {e}")
            self.close()
            return False

    def close(self):
        self._stop.set()
        if self._reader and self._reader.is_alive():
            self._reader.join(timeout=0.6)
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        self.ser = None
        self.port = None
        self._emit_conn(False)

    def write_line(self, cmd: str) -> bool:
        """Write a single command (appends eol if missing). Returns True on success."""
        if not self.ser or not self.ser.is_open:
            return False
        try:
            if not cmd.endswith(self.eol):
                cmd = cmd + self.eol
            # keep responses fresh
            self.ser.reset_input_buffer()
            self.ser.write(cmd.encode("utf-8"))
            self.ser.flush()
            return True
        except Exception as e:
            self._log_app(f"Send error: {e}")
            return False

    # ---------- reader thread ----------
    def _start_reader(self):
        self._stop.clear()
        self._reader = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader.start()

    def _reader_loop(self):
        s = self.ser
        while s and s.is_open and not self._stop.is_set():
            try:
                raw = s.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="ignore").strip()
                if line:
                    self._log_rx(line)
            except Exception as e:
                self._log_app(f"Serial read error: {e}")
                break
