# ADU control panel
import customtkinter as ctk
import yaml

class ADUPanel(ctk.CTkFrame):
    def __init__(self, master, bus):
        super().__init__(master)
        self.bus = bus
        ctk.CTkLabel(self, text="ADU Control").pack(pady=(8,4))
        with open("config/commands.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        row = ctk.CTkFrame(self); row.pack(padx=8, pady=4)
        for i, b in enumerate(cfg.get("adu_buttons", [])):
            ctk.CTkButton(row, text=b["label"],
                          command=lambda act=b["action"]: self._do(act)
                          ).grid(row=i//1, column=0, padx=4, pady=4, sticky="ew")

    def _do(self, action: str):
        # TODO: call real ADU client; for now just log
        self.bus.publish("log:line", f"[ADU] {action} (stub)")
