# gui/adu_gui.py

import customtkinter as ctk
from utils.adu_utils import open_adu_device, close_adu_device, write_device


class ADUFrame(ctk.CTkFrame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # UI Setup
        ctk.CTkLabel(self, text="ADU Switch Control").pack(pady=5)
        ctk.CTkButton(self, text="Power ON", command=self.power_on).pack(pady=5)
        ctk.CTkButton(self, text="Power OFF", command=self.power_off).pack(pady=5)
        ctk.CTkButton(self, text="USB ON", command=self.usb_on).pack(pady=5)
        ctk.CTkButton(self, text="USB OFF", command=self.usb_off).pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="Status: Initializing...")
        self.status_label.pack(pady=5)

        # ADU Init
        self.adu_handle = open_adu_device()
        if self.adu_handle:
            self.status_label.configure(text="Status: Connected")
        else:
            self.status_label.configure(text="Status: Disconnected")

    def send_command(self, cmd):
        if self.adu_handle:
            print(f"ADU: Sending {cmd}")
            write_device(self.adu_handle, cmd)
        else:
            print("ADU: Device handle not available")

    def power_on(self):
        self.send_command("sk0")

    def power_off(self):
        self.send_command("rk0")

    def usb_on(self):
        self.send_command("sk1")

    def usb_off(self):
        self.send_command("rk1")

    def on_close(self):
        """Safely close the ADU connection on app exit."""
        if self.adu_handle:
            close_adu_device(self.adu_handle)
