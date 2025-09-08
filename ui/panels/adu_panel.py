# ui/panels/adu_panel.py
import customtkinter as ctk
import yaml

APP_TAG = "<UDC app>"

class ADUPanel(ctk.CTkFrame):
    def __init__(self, master, bus, adu_client, cfg_path="config/commands.yaml"):
        super().__init__(master)
        self.bus = bus
        self.adu = adu_client

        ctk.CTkLabel(self, text="ADU Control").pack(pady=(8,4))

        # Row: Connect / Disconnect
        row_conn = ctk.CTkFrame(self); row_conn.pack(fill="x", padx=8, pady=(0,6))
        ctk.CTkButton(row_conn, text="Connect", width=100, command=self._connect).pack(side="left", padx=(0,6))
        ctk.CTkButton(row_conn, text="Disconnect", width=100, command=self._disconnect).pack(side="left")

        # Status badge directly under the buttons & label (as requested)
        self.state_var = ctk.StringVar(value="DISCONNECTED")
        self.state_lbl = ctk.CTkLabel(self, textvariable=self.state_var,
                                      fg_color="#B00020", text_color="white",
                                      corner_radius=6, padx=8, pady=4)
        self.state_lbl.pack(pady=(6,8))

        # Actions in a 2×2 grid:
        # USB ON | Light ON
        # USB OFF| Light OFF
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        mapping = {b["label"]: b["action"] for b in cfg.get("adu_buttons", [])}

        grid = ctk.CTkFrame(self); grid.pack(padx=8, pady=4)
        def button(label, r, c):
            ctk.CTkButton(grid, text=label,
                          command=lambda act=mapping.get(label): self._do(act)
                          ).grid(row=r, column=c, padx=4, pady=4, sticky="ew")

        button("USB ON",  0, 0)
        button("Light ON",0, 1)
        button("USB OFF", 1, 0)
        button("Light OFF",1, 1)

    # --------- actions ----------
    def _connect(self):
        ok = self.adu.connect()
        if ok:
            self.state_var.set("CONNECTED"); self.state_lbl.configure(fg_color="#1B5E20")
            self.bus.publish("log:line", f"{APP_TAG} ADU connected")
        else:
            self.state_var.set("DISCONNECTED"); self.state_lbl.configure(fg_color="#B00020")
            self.bus.publish("log:line", f"{APP_TAG} ADU connect failed")

    def _disconnect(self):
        self.adu.disconnect()
        self.state_var.set("DISCONNECTED"); self.state_lbl.configure(fg_color="#B00020")
        self.bus.publish("log:line", f"{APP_TAG} ADU disconnected")

    def _do(self, action: str | None):
        if not action:
            self.bus.publish("log:line", f"{APP_TAG} [ADU] Unknown action")
            return
        ok = self.adu.action(action)
        self.bus.publish("log:line", f"{APP_TAG} [ADU] {action} -> {'OK' if ok else 'FAIL'}")
