# gui_main

import customtkinter as ctk
from gui.camera_gui import CameraFrame
from gui.servo_gui import ServoFrame
from gui.magnet_gui import MagnetFrame
from controllers.shared_serial import get_shared_serial_connection
from gui.adu_gui import ADUFrame

from utils.version import __version__
print(f"App Version: {__version__}")


shared_serial = get_shared_serial_connection()



def launch_gui():
    app = ctk.CTk()
    app.title("Unified Device Control GUI")
    app.geometry("1200x800")
    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(1, weight=1)
    # app = ctk.CTk()
    app.title(f"Unified Device Control GUI - v{__version__}")


    # === Status Bar ===
    status_label = ctk.CTkLabel(app, text="Status: Ready", anchor="w")
    status_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

    # === Camera Frame ===
    camera_frame = CameraFrame(app)
    camera_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    # === Servo Frame ===
    servo_frame = ServoFrame(app, serial_connection=shared_serial)
    servo_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

    # === Magnet Frame ===
    magnet_frame = MagnetFrame(app, serial_connection=shared_serial)
    magnet_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    # === ADU Frame ===
    adu_frame = ADUFrame(app)
    adu_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

    # === Bottom Controls ===
    bottom_frame = ctk.CTkFrame(app)
    bottom_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    ctk.CTkButton(bottom_frame, text="System Check").pack(side="left", padx=10, pady=10)
    ctk.CTkButton(bottom_frame, text="Exit", command=app.destroy).pack(side="right", padx=10, pady=10)

    app.mainloop()
