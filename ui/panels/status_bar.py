# Status bar widget
import customtkinter as ctk
import time

class StatusBar(ctk.CTkFrame):
    def __init__(self, master, initial="Ready"):
        super().__init__(master)
        self.start = time.time()
        self.label = ctk.CTkLabel(self, text=f"Status: {initial}", anchor="w")
        self.label.pack(side="left", padx=8, pady=4)
        self.uptime = ctk.CTkLabel(self, text="00:00:00", anchor="e")
        self.uptime.pack(side="right", padx=8, pady=4)

    def set(self, text, color=None):
        self.label.configure(text=f"Status: {text}")
        if color:
            # simple color hint via emoji dot
            dot = {"green":"🟢","red":"🔴","blue":"🔵","yellow":"🟡","gray":"⚪"}.get(color,"")
            self.label.configure(text=f"{dot} Status: {text}")

    def tick(self):
        secs = int(time.time() - self.start)
        h,m,s = secs//3600, (secs%3600)//60, secs%60
        self.uptime.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self.tick)
