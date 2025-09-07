# Arduino command panel
import customtkinter as ctk
import yaml

class ArduinoPanel(ctk.CTkFrame):
    def __init__(self, master, serial_manager, bus):
        super().__init__(master)
        self.serial = serial_manager
        self.bus = bus
        ctk.CTkLabel(self, text="Arduino Control").pack(pady=(8,4))
        with open("config/commands.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        btns = cfg.get("arduino_buttons", [])
        grid = ctk.CTkFrame(self); grid.pack(padx=8, pady=4)
        # buttons in 2 columns
        for i, b in enumerate(btns):
            r, c = divmod(i, 2)
            ctk.CTkButton(grid, text=b["label"],
                           command=lambda cmd=b["cmd"]: self.send(cmd)
                          ).grid(row=r, column=c, padx=4, pady=4, sticky="ew")
        # manual send
        row = ctk.CTkFrame(self); row.pack(fill="x", padx=8, pady=(8,8))
        self.entry = ctk.CTkEntry(row, placeholder_text="manual command")
        self.entry.pack(side="left", expand=True, fill="x", padx=4)
        ctk.CTkButton(row, text="Send", command=self.send_entry).pack(side="left", padx=4)

    def send_entry(self):
        txt = self.entry.get().strip()
        if txt: self.send(txt)

    def send(self, cmd: str):
        ok = self.serial.write_line(cmd)
        if ok:
            self.bus.publish("log:line", f"→ {cmd}")
        else:
            self.bus.publish("log:line", f"[ERR] write failed (not connected)")
