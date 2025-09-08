# ui/main_window.py
# Main CTk window

import customtkinter as ctk
import logging
import os, sys

from ui.panels.status_bar import StatusBar
from ui.panels.camera_panel import DualCameraPanel
from ui.panels.arduino_panel import ArduinoPanel
from ui.panels.adu_panel import ADUPanel
from ui.panels.log_panel import LogPanel
from core.serial_manager import SerialManager
from core.device_scanner import DeviceScanner
from core.event_bus import EventBus
from core.adu_client import ADUClient


class MainWindow(ctk.CTk):
    def __init__(self, app_cfg, logfile, version):
        super().__init__()

        # ---- window/meta ----
        title = f'{app_cfg["app"]["name"]} – {app_cfg["app"]["version_tag"]}'
        self.title(title)
        self.geometry("1400x930")
        self.minsize(1200, 760)

        # ---- infra / services ----
        self.bus = EventBus()
        self.serial = SerialManager(
            self.bus,
            baud=app_cfg["serial"]["baudrate"],
            eol=app_cfg["serial"]["eol"],
        )
        self.scanner = DeviceScanner(self.bus, app_cfg["serial"])

        # Ensure Python can import the ontrak package if it's under utils/...
        adu_cfg = app_cfg.get("adu", {})
        dll_dir = adu_cfg.get("dll_dir")
        if dll_dir:
            pkg_root = os.path.abspath(os.path.join(dll_dir, os.pardir))
            if pkg_root not in sys.path:
                sys.path.append(pkg_root)

        self.adu_client = ADUClient(
            bus=self.bus,
            product_id=adu_cfg.get("product_id", 218),
            dll_dir=dll_dir,
            action_map=adu_cfg.get("action_map"),
            timeout_ms=adu_cfg.get("timeout_ms", 5000),
            serial=adu_cfg.get("serial"),
        )

        # ---- grid (3 cols x 3 rows) ----
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)  # actions column
        self.grid_rowconfigure(1, weight=1)    # cameras row
        self.grid_rowconfigure(2, weight=1)    # log row

        # ---- status bar (row 0) ----
        self.status = StatusBar(self, initial="Ready")
        self.status.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(8, 2))

        # ---- cameras (row 1, col 0-1) ----
        self.cameras = DualCameraPanel(self, app_cfg["cameras"], self.bus)
        self.cameras.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        # ---- serial monitor (row 2, col 0-1) ----
        self.log_panel = LogPanel(
            self,
            also_log_to_file=app_cfg["logging"].get("also_log_serial", True),
        )
        self.log_panel.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        # ---- right actions column (row 1-2, col 2) ----
        self.actions = ctk.CTkFrame(self)
        self.actions.grid(row=1, column=2, rowspan=2, sticky="ns", padx=(0, 10), pady=10)
        for i in range(10):
            self.actions.grid_rowconfigure(i, weight=0)
        self.actions.grid_rowconfigure(99, weight=1)

        # Arduino panel (now owns Scan / Connect / Disconnect)
        self.arduino = ArduinoPanel(self.actions, self.serial, self.bus, scanner=self.scanner)
        self.arduino.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # ADU panel (status badge placed under Connect/Disconnect inside the panel)
        self.adu = ADUPanel(self.actions, self.bus, self.adu_client)
        self.adu.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # Right-column actions (kept: System Check & Exit)
        self.syscheck_btn = ctk.CTkButton(self.actions, text="System Check", command=self.on_syscheck)
        self.syscheck_btn.grid(row=13, column=0, sticky="ew", padx=10, pady=(20, 5))

        self.exit_btn = ctk.CTkButton(self.actions, text="Exit", fg_color="#444", command=self.destroy)
        self.exit_btn.grid(row=99, column=0, sticky="ew", padx=10, pady=(40, 0))

        # ---- event subscriptions ----
        self.bus.subscribe("log:line", lambda payload: self.log_panel.append(payload))
        self.bus.subscribe("conn:state", self._on_conn_state)
        self.bus.subscribe("scan:result", self._on_scan_result)

        # timers
        self.after(250, self.status.tick)
        self.after(200, self.cameras.apply_startup)

    # ---------------- actions ----------------
    def on_syscheck(self):
        logging.info("System Check clicked (stub for now)")
        self.status.set("System Check running…", color="yellow")

    # ---------------- bus handlers ----------------
    def _on_conn_state(self, payload):
        connected = bool(payload.get("connected"))
        txt = "Connected" if connected else "Disconnected"
        self.status.set(txt, color="green" if connected else "gray")

    def _on_scan_result(self, payload):
        best = payload.get("best")
        msg = f"Scan complete. Best: {best or 'None'}"
        self.status.set(msg, color="blue")
        self.log_panel.append(f"[SCAN] {msg}")
