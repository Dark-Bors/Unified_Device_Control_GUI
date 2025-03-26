import customtkinter as ctk

def launch_gui():
    app = ctk.CTk()
    app.title("Unified Device Control GUI")
    app.geometry("1200x800")
    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(1, weight=1)

    # === Status Bar ===
    status_label = ctk.CTkLabel(app, text="Status: Ready", anchor="w")
    status_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

    # === Camera Frame ===
    camera_frame = ctk.CTkFrame(app)
    camera_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(camera_frame, text="Camera Control").pack(pady=5)

    # === Servo Frame ===
    servo_frame = ctk.CTkFrame(app)
    servo_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(servo_frame, text="Servo Control").pack(pady=5)

    # === Magnet Frame ===
    magnet_frame = ctk.CTkFrame(app)
    magnet_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(magnet_frame, text="Magnet Control").pack(pady=5)

    # === ADU Frame ===
    adu_frame = ctk.CTkFrame(app)
    adu_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(adu_frame, text="ADU Control").pack(pady=5)

    # === Bottom Controls ===
    bottom_frame = ctk.CTkFrame(app)
    bottom_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    ctk.CTkButton(bottom_frame, text="System Check").pack(side="left", padx=10, pady=10)
    ctk.CTkButton(bottom_frame, text="Exit", command=app.destroy).pack(side="right", padx=10, pady=10)

    app.mainloop()
