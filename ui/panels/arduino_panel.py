# ui/panels/arduino_panel.py
import customtkinter as ctk
import yaml

APP_TAG = "<UDC app>"

class ArduinoPanel(ctk.CTkFrame):
    def __init__(self, master, serial_manager, bus, scanner=None):
        super().__init__(master)
        self.serial = serial_manager
        self.bus = bus
        self.scanner = scanner

        ctk.CTkLabel(self, text="Arduino Control").pack(pady=(8,4))

        # ---- Controls row: Scan / Connect / Disconnect ----
        row_ctrl = ctk.CTkFrame(self); row_ctrl.pack(fill="x", padx=8, pady=(0,6))
        self.btn_scan = ctk.CTkButton(row_ctrl, text="Scan Ports (PING)", width=150,
                                      command=self._scan_ports)
        self.btn_scan.pack(side="left", padx=(0,6))
        self.btn_connect = ctk.CTkButton(row_ctrl, text="Connect (last scan)", width=150,
                                         command=self._connect_best)
        self.btn_connect.pack(side="left", padx=6)
        self.btn_disc = ctk.CTkButton(row_ctrl, text="Disconnect", width=120,
                                      command=self._disconnect)
        self.btn_disc.pack(side="left", padx=6)

        # ---- Local connection badge (under the controls) ----
        self.conn_var = ctk.StringVar(value="DISCONNECTED")
        self.conn_lbl = ctk.CTkLabel(self, textvariable=self.conn_var,
                                     fg_color="#B00020", text_color="white",
                                     corner_radius=6, padx=8, pady=4)
        self.conn_lbl.pack(pady=(6,8))

        # Subscribe to serial status and (for logging) scan result
        self.bus.subscribe("conn:state", self._on_conn_state)
        self.bus.subscribe("scan:result", self._on_scan_result)

        # ---- Command buttons from YAML ----
        with open("config/commands.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        btns = cfg.get("arduino_buttons", [])
        grid = ctk.CTkFrame(self); grid.pack(padx=8, pady=4)
        for i, b in enumerate(btns):
            r, c = divmod(i, 2)
            ctk.CTkButton(grid, text=b["label"],
                          command=lambda cmd=b["cmd"]: self._send(cmd)
                          ).grid(row=r, column=c, padx=4, pady=4, sticky="ew")

        # ---- Manual send ----
        row = ctk.CTkFrame(self); row.pack(fill="x", padx=8, pady=(8,8))
        self.entry = ctk.CTkEntry(row, placeholder_text="manual command")
        self.entry.pack(side="left", expand=True, fill="x", padx=4)
        ctk.CTkButton(row, text="Send", command=self._send_entry).pack(side="left", padx=4)

    # ---------- callbacks ----------
    def _scan_ports(self):
        if not self.scanner:
            self.bus.publish("log:line", f"{APP_TAG} [ERR] Scanner not available")
            return

        # one-shot subscriber that auto-connects to the best port
        def _after_scan(payload):
            best = payload.get("best")
            if best:
                self.bus.publish("log:line", f"{APP_TAG} Auto-connect -> {best}")
                ok = self.serial.open(best)
                self.bus.publish("log:line", f"{APP_TAG} Connect {best} -> {'OK' if ok else 'FAIL'}")
            # unsubscribe this one-shot callback (guard if your EventBus lacks unsubscribe)
            try:
                self.bus.unsubscribe("scan:result", _after_scan)  # if you implemented it
            except Exception:
                pass

        try:
            self.bus.subscribe("scan:result", _after_scan)
        except Exception:
            # if the bus doesn’t support dup-subs, it’s fine; the guard above will keep it harmless
            pass

        self.bus.publish("log:line", f"{APP_TAG} Scanning ports…")
        self.scanner.scan_async()

    def _connect_best(self):
        port = getattr(self.scanner, "best_port", None)
        if not port:
            self.bus.publish("log:line", f"{APP_TAG} No best port yet (Scan first).")
            return
        ok = self.serial.open(port)
        self.bus.publish("log:line", f"{APP_TAG} Connect {port} -> {'OK' if ok else 'FAIL'}")

    def _disconnect(self):
        self.serial.close()
        self.bus.publish("log:line", f"{APP_TAG} Disconnected")

    def _send_entry(self):
        txt = self.entry.get().strip()
        if txt: self._send(txt)

    def _send(self, cmd: str):
        ok = self.serial.write_line(cmd)
        if ok:
            self.bus.publish("log:line", f"{APP_TAG} → {cmd}")
        else:
            self.bus.publish("log:line", f"{APP_TAG} [ERR] write failed (not connected)")

    def _on_conn_state(self, payload: dict):
        ok = bool(payload.get("connected"))
        port = payload.get("port")
        if ok and port:
            self.conn_var.set(f"CONNECTED {port}")
            self.conn_lbl.configure(fg_color="#1B5E20")
        else:
            self.conn_var.set("DISCONNECTED")
            self.conn_lbl.configure(fg_color="#B00020")

    def _on_scan_result(self, payload: dict):
        # just log; auto-connect handled in _scan_ports one-shot
        best = payload.get("best")
        ports = payload.get("ports", [])
        txt = f"Scan: best={best or 'None'} | ports={', '.join(ports) or 'None'}"
        self.bus.publish("log:line", f"{APP_TAG} {txt}")
