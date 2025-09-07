# Main CTk window
import customtkinter as ctk
import logging
from ui.panels.status_bar import StatusBar
from ui.panels.camera_panel import DualCameraPanel
from ui.panels.arduino_panel import ArduinoPanel
from ui.panels.adu_panel import ADUPanel
from ui.panels.log_panel import LogPanel
from core.serial_manager import SerialManager
from core.device_scanner import DeviceScanner
from core.event_bus import EventBus

class MainWindow(ctk.CTk):
    def __init__(self, app_cfg, logfile, version):
        super().__init__()
        self.title(f'{app_cfg["app"]["name"]} – {app_cfg["app"]["version_tag"]}')
        self.geometry("1400x930")
        self.minsize(1200, 760)

        self.bus = EventBus()
        self.serial = SerialManager(self.bus, baud=app_cfg["serial"]["baudrate"],
                                    eol=app_cfg["serial"]["eol"])
        self.scanner = DeviceScanner(self.bus, app_cfg["serial"])

        # GRID: 3 cols (main area + main area + narrow actions); 3 rows
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)  # actions
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Status bar (row 0, span all)
        self.status = StatusBar(self, initial="Ready")
        self.status.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(8,2))

        # Cameras (row 1, col 0-1)
        self.cameras = DualCameraPanel(self, app_cfg["cameras"], self.bus)
        self.cameras.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        # Serial Monitor (row 2, col 0-1) — wide
        self.log_panel = LogPanel(self, also_log_to_file=app_cfg["logging"].get("also_log_serial", True))
        self.log_panel.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0,10))

        # Right actions column (row 1-2, col 2)
        self.actions = ctk.CTkFrame(self)
        self.actions.grid(row=1, column=2, rowspan=2, sticky="ns", padx=(0,10), pady=10)
        for i in range(10): self.actions.grid_rowconfigure(i, weight=0)
        self.actions.grid_rowconfigure(99, weight=1)

        # Arduino & ADU mini-panels (stacked)
        self.arduino = ArduinoPanel(self.actions, self.serial, self.bus)
        self.arduino.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.adu = ADUPanel(self.actions, self.bus)  # actual impl later
        self.adu.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # Action buttons
        self.scan_btn = ctk.CTkButton(self.actions, text="Scan", command=self.on_scan)
        self.scan_btn.grid(row=10, column=0, sticky="ew", padx=10, pady=(20,5))

        self.connect_btn = ctk.CTkButton(self.actions, text="Connect", command=self.on_connect)
        self.connect_btn.grid(row=11, column=0, sticky="ew", padx=10, pady=5)

        self.disconnect_btn = ctk.CTkButton(self.actions, text="Disconnect", command=self.on_disconnect)
        self.disconnect_btn.grid(row=12, column=0, sticky="ew", padx=10, pady=5)

        self.syscheck_btn = ctk.CTkButton(self.actions, text="System Check", command=self.on_syscheck)
        self.syscheck_btn.grid(row=13, column=0, sticky="ew", padx=10, pady=(20,5))

        self.exit_btn = ctk.CTkButton(self.actions, text="Exit", fg_color="#444", command=self.destroy)
        self.exit_btn.grid(row=99, column=0, sticky="ew", padx=10, pady=(40,0))

        # Subscribe to events → push into monitor + status
        self.bus.subscribe("log:line", lambda payload: self.log_panel.append(payload))
        self.bus.subscribe("conn:state", self._on_conn_state)
        self.bus.subscribe("scan:result", self._on_scan_result)
        self.after(250, self.status.tick)  # uptime timer

        # Start cameras per config
        self.after(200, self.cameras.apply_startup)

    # Actions
    def on_scan(self):
        self.status.set("Scanning ports…", color="blue")
        self.scanner.scan_async()

    def on_connect(self):
        port = self.scanner.best_port or self.serial.port  # from scan
        ok = self.serial.open(port)
        self.status.set(f"Connected {port}" if ok else "Connect failed", color="green" if ok else "red")

    def on_disconnect(self):
        self.serial.close()
        self.status.set("Disconnected", color="gray")

    def on_syscheck(self):
        logging.info("System Check clicked (stub for now)")
        self.status.set("System Check running…", color="yellow")

    # Event handlers
    def _on_conn_state(self, payload):
        txt = "Connected" if payload.get("connected") else "Disconnected"
        self.status.set(txt, color="green" if payload.get("connected") else "gray")

    def _on_scan_result(self, payload):
        best = payload.get("best")
        msg = f"Scan complete. Best: {best or 'None'}"
        self.status.set(msg, color="blue")
        self.log_panel.append(f"[SCAN] {msg}")
