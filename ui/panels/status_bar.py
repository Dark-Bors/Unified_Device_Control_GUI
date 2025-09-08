# ui/panels/status_bar.py
import customtkinter as ctk
import time
from typing import Dict, Optional

# Simple tooltip for CustomTkinter widgets
class _Tooltip(ctk.CTkToplevel):
    def __init__(self, widget, text: str):
        super().__init__(widget)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#222222")
        self.label = ctk.CTkLabel(self, text=text, padx=8, pady=6)
        self.label.pack()
        self.widget = widget
        self.text = text

    def show(self, x: int, y: int):
        self.label.configure(text=self.text)
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self):
        self.withdraw()


class StatusBar(ctk.CTkFrame):
    """
    Usage (backwards-compatible with your calls):
        status.set("Scanning ports…", color="blue")
        status.set("Connected COM3", color="green")
        status.set("Connect failed", color="red")
        status.set("Ready", color="gray")

    Colors & meanings (hover over the colored pill to see legend):
        green  -> Connected / OK
        blue   -> Scanning / Working
        yellow -> Running / Pending user action
        red    -> Error / Failure
        gray   -> Idle / Disconnected
    """
    DEFAULT_COLOR_MAP: Dict[str, str] = {
        "green":  "#1B5E20",
        "blue":   "#0D47A1",
        "yellow": "#B8860B",
        "red":    "#B00020",
        "gray":   "#616161",
    }

    DEFAULT_MEANINGS: Dict[str, str] = {
        "green":  "Connected / OK",
        "blue":   "Scanning / Working",
        "yellow": "Running / Waiting",
        "red":    "Error / Failure",
        "gray":   "Idle / Disconnected",
    }

    def __init__(self, master, initial="Ready",
                 color_map: Optional[Dict[str, str]] = None,
                 meanings: Optional[Dict[str, str]] = None):
        super().__init__(master)

        self.start = time.time()
        self.color_map = {**self.DEFAULT_COLOR_MAP, **(color_map or {})}
        self.meanings  = {**self.DEFAULT_MEANINGS, **(meanings or {})}

        # Left: colored pill + text
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=6, pady=4, fill="x")

        # Colored pill (a small rounded label)
        self.dot = ctk.CTkLabel(left, text="", width=16, height=16,
                                corner_radius=8, fg_color=self.color_map["gray"])
        self.dot.pack(side="left", padx=(6, 8))

        # Tooltip for the dot
        self._tooltip = _Tooltip(self.dot, self._legend_text())
        self.dot.bind("<Enter>", self._on_enter)
        self.dot.bind("<Leave>", self._on_leave)
        self.dot.bind("<Motion>", self._on_motion)

        # Status text
        self.label = ctk.CTkLabel(left, text=f"Status: {initial}", anchor="w")
        self.label.pack(side="left", padx=2)

        # Right: uptime
        self.uptime = ctk.CTkLabel(self, text="00:00:00", anchor="e")
        self.uptime.pack(side="right", padx=8, pady=4)

        # Kick off uptime timer
        self.after(1000, self.tick)

    # ------- public API (keeps your old signature) -------
    def set(self, text: str, color: Optional[str] = None):
        """Update the status text and (optionally) change the colored pill."""
        self.label.configure(text=f"Status: {text}")
        if color:
            self._set_color(color)

    # ------- internals -------
    def _set_color(self, color_key: str):
        color = self.color_map.get(color_key, self.color_map["gray"])
        self.dot.configure(fg_color=color)

    def _legend_text(self) -> str:
        lines = [f"● {name}: {self.meanings.get(name, '')}"
                 for name in ["green", "blue", "yellow", "red", "gray"]]
        return "Status legend:\n" + "\n".join(lines)

    # Tooltip handlers
    def _on_enter(self, event):
        # place slightly below the cursor
        x = self.dot.winfo_rootx() + event.x + 12
        y = self.dot.winfo_rooty() + event.y + 16
        self._tooltip.show(x, y)

    def _on_leave(self, _):
        self._tooltip.hide()

    def _on_motion(self, event):
        x = self.dot.winfo_rootx() + event.x + 12
        y = self.dot.winfo_rooty() + event.y + 16
        self._tooltip.show(x, y)

    def tick(self):
        secs = int(time.time() - self.start)
        h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
        self.uptime.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self.tick)
