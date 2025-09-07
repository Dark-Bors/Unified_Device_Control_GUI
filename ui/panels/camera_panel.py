# Dual camera panel
import customtkinter as ctk
from core.camera_worker import CameraWorker
from PIL import ImageTk, Image
import cv2
import os, time

class CamTile(ctk.CTkFrame):
    def __init__(self, master, name, cfg, bus):
        super().__init__(master)
        self.name, self.cfg, self.bus = name, cfg, bus
        self.lbl = ctk.CTkLabel(self, text=f"{name} (OFF)", width=640, height=480)
        self.lbl.pack(padx=6, pady=6)
        row = ctk.CTkFrame(self); row.pack(pady=(0,6))
        self.toggle = ctk.CTkSwitch(row, text=f"{name} ON", command=self._toggle)
        self.toggle.pack(side="left", padx=6)
        self.snap_btn = ctk.CTkButton(row, text="Snapshot", command=self.snapshot)
        self.snap_btn.pack(side="left", padx=6)
        self.rec_btn = ctk.CTkSwitch(row, text="Record", command=self._rec_toggle)
        self.rec_btn.pack(side="left", padx=6)
        self.worker = None
        self.recording = False
        self.out = None

    def apply_startup(self):
        if self.cfg.get("enabled_on_start", False):
            self.toggle.select(); self._toggle()

    def _toggle(self):
        if self.toggle.get():
            self.worker = CameraWorker(
                index=self.cfg["index"],
                width=self.cfg["width"],
                height=self.cfg["height"],
                target_fps=self.cfg["target_fps"],
                on_frame=self._on_frame,
            )
            self.worker.start()

            # Verify open shortly after starting (non-blocking)
            def verify_open():
                # if worker disappeared or camera failed to open, revert switch
                if (not self.worker) or (self.worker.cap is None) or (not self.worker.cap.isOpened()):
                    # deselect -> triggers the else branch below to clean up UI
                    self.toggle.deselect()
                    self._toggle()
                    # log through the bus we already have on self
                    if hasattr(self, "bus") and self.bus:
                        self.bus.publish("log:line", f"[{self.name}] Camera not available")

            self.after(300, verify_open)
            self.lbl.configure(text="")  # clear placeholder

        else:
            # OFF: stop worker and writer cleanly
            if self.worker:
                try:
                    self.worker.stop()
                finally:
                    self.worker = None

            if self.out:
                try:
                    self.out.release()
                finally:
                    self.out = None

            self.rec_btn.deselect()
            self.recording = False
            self.lbl.configure(text=f"{self.name} (OFF)", image=None)


    def _rec_toggle(self):
        self.recording = bool(self.rec_btn.get())
        if self.recording and self.worker and self.worker.last_frame is not None:
            os.makedirs("captures", exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            codec = cv2.VideoWriter_fourcc(*"mp4v")
            w,h = self.worker.size
            self.out = cv2.VideoWriter(os.path.join("captures", f"{self.name}_{ts}.mp4"), codec, 20, (w,h))
        else:
            if self.out: self.out.release(); self.out=None

    def snapshot(self):
        if self.worker and self.worker.last_frame is not None:
            os.makedirs("captures", exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            path = os.path.join("captures", f"{self.name}_{ts}.png")
            cv2.imwrite(path, self.worker.last_frame_bgr)
            self.bus.publish("log:line", f"[{self.name}] Snapshot saved: {path}")

    def _on_frame(self, frame_bgr):
        # display
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        img = img.resize((640, 480))
        imgtk = ImageTk.PhotoImage(img)
        self.lbl.configure(image=imgtk); self.lbl.image = imgtk
        # record
        if self.recording and self.out is not None:
            self.out.write(frame_bgr)

class DualCameraPanel(ctk.CTkFrame):
    def __init__(self, master, cameras_cfg, bus):
        super().__init__(master)
        self.cam_a = CamTile(self, "CamA", cameras_cfg["cam_a"], bus)
        self.cam_b = CamTile(self, "CamB", cameras_cfg["cam_b"], bus)
        self.cam_a.grid(row=0, column=0, padx=6, pady=6, sticky="n")
        self.cam_b.grid(row=0, column=1, padx=6, pady=6, sticky="n")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def apply_startup(self):
        self.cam_a.apply_startup()
        self.cam_b.apply_startup()
