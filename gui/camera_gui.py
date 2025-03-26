# camera_gui

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading


class CameraFrame(ctk.CTkFrame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.camera_label = ctk.CTkLabel(self, text="Camera Feed")
        self.camera_label.pack(padx=10, pady=10)

        self.cap = None
        self.running = False

        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Start Camera", command=self.start_camera).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Stop Camera", command=self.stop_camera).pack(side="left", padx=5)

    def start_camera(self):
        if not self.running:
            self.cap = cv2.VideoCapture(1)
            self.running = True
            threading.Thread(target=self.update_frame, daemon=True).start()

    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
            self.camera_label.configure(text="Camera Feed", image=None)

    def update_frame(self):
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(img)
                self.camera_label.configure(image=imgtk, text="")
                self.camera_label.image = imgtk
            self.after(30, lambda: None)  # Keep Tkinter happy

    def on_close(self):
        self.stop_camera()
