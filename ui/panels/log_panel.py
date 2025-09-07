# Serial monitor panel
import customtkinter as ctk
import time, logging

class LogPanel(ctk.CTkFrame):
    def __init__(self, master, also_log_to_file=True):
        super().__init__(master)
        top = ctk.CTkFrame(self); top.pack(fill="x", padx=6, pady=(6,0))
        self.search = ctk.CTkEntry(top, placeholder_text="search…")
        self.search.pack(side="left", padx=6, pady=6)
        ctk.CTkButton(top, text="Clear", command=self.clear).pack(side="right", padx=6)
        ctk.CTkButton(top, text="Save Log Copy", command=self.save_copy).pack(side="right", padx=6)

        self.txt = ctk.CTkTextbox(self, height=240)
        self.txt.pack(expand=True, fill="both", padx=6, pady=6)
        self.also_log_to_file = also_log_to_file

    def append(self, line: str):
        ts = time.strftime("%H:%M:%S")
        self.txt.insert("end", f"{ts}  {line}\n")
        self.txt.see("end")
        if self.also_log_to_file:
            logging.info("[SERIAL] %s", line)

    def clear(self):
        self.txt.delete("1.0", "end")

    def save_copy(self):
        # quick copy into logs/ with timestamp
        import os, time
        os.makedirs("logs", exist_ok=True)
        path = os.path.join("logs", f"user_saved_{time.strftime('%Y%m%d-%H%M%S')}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.txt.get("1.0","end").strip())
