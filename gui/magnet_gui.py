# magnet_gui.py

import customtkinter as ctk

class MagnetFrame(ctk.CTkFrame):
    def __init__(self, master, serial_connection=None, *args, **kwargs):
        self.serial_connection = serial_connection  # Catch custom argument before super()
        super().__init__(master, *args, **kwargs)

        ctk.CTkLabel(self, text="Magnet Control").pack(pady=5)
        ctk.CTkButton(self, text="Magnet ON", command=self.magnet_on).pack(pady=5)
        ctk.CTkButton(self, text="Magnet OFF", command=self.magnet_off).pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="Status: Disconnected")
        self.status_label.pack(pady=5)

        if self.serial_connection and self.serial_connection.is_open:
            self.status_label.configure(text="Status: Connected (shared)")

    def send_command(self, cmd):
        if self.serial_connection and self.serial_connection.is_open:
            print(f"[MagnetFrame] Sending: {cmd}")
            self.serial_connection.write(f"{cmd}\n".encode())
        else:
            print("[MagnetFrame] Not connected")

    def magnet_on(self):
        self.send_command("ON")

    def magnet_off(self):
        self.send_command("OFF")
