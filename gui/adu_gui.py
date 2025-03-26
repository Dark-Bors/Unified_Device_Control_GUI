# gui/adu_gui.py

import customtkinter as ctk


class ADUFrame(ctk.CTkFrame):
    def __init__(self, master, serial_connection=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.serial_connection = serial_connection

        # UI Components
        ctk.CTkLabel(self, text="ADU Switch Control").pack(pady=5)

        ctk.CTkButton(self, text="Power ON", command=self.power_on).pack(pady=5)
        ctk.CTkButton(self, text="Power OFF", command=self.power_off).pack(pady=5)
        ctk.CTkButton(self, text="USB ON", command=self.usb_on).pack(pady=5)
        ctk.CTkButton(self, text="USB OFF", command=self.usb_off).pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="Status: Disconnected")
        self.status_label.pack(pady=5)

        if self.serial_connection and self.serial_connection.is_open:
            self.status_label.configure(text="Status: Connected (shared)")

    def send_command(self, cmd):
        if self.serial_connection and self.serial_connection.is_open:
            print(f"ADU: Sending {cmd}")
            self.serial_connection.write(f"{cmd}\n".encode())
        else:
            print("ADU: Serial connection not available")

    def power_on(self):
        self.send_command("POWER_ON")

    def power_off(self):
        self.send_command("POWER_OFF")

    def usb_on(self):
        self.send_command("USB_ON")

    def usb_off(self):
        self.send_command("USB_OFF")
