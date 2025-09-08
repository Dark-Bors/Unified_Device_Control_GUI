# ui/panels/camera_panel.py
# Dual camera panel (CTkImage updates on main thread, robust toggles, safe image clearing)

import os, time
import cv2
import customtkinter as ctk
from PIL import Image
from core.camera_worker import CameraWorker


class CamTile(ctk.CTkFrame):
    def __init__(self, master, name, cfg, bus):
        super().__init__(master)
        self.name, self.cfg, self.bus = name, cfg, bus

        # Display
        self.lbl = ctk.CTkLabel(self, text=f"{name} (OFF)", width=640, height=480)
        self.lbl.pack(padx=6, pady=6)

        # Controls
        row = ctk.CTkFrame(self)
        row.pack(pady=(0, 6))
        self.toggle = ctk.CTkSwitch(row, text=f"{name} ON", command=self._toggle)
        self.toggle.pack(side="left", padx=6)
        self.snap_btn = ctk.CTkButton(row, text="Snapshot", command=self.snapshot)
        self.snap_btn.pack(side="left", padx=6)
        self.rec_btn = ctk.CTkSwitch(row, text="Record", command=self._rec_toggle)
        self.rec_btn.pack(side="left", padx=6)

        # State
        self.worker = None
        self.recording = False
        self.out = None

        # UI image state
        self._img_gen = 0
        self._ctk_img = None       # strong reference to CTkImage
        self._start_ts = None      # for open timeout

    # ---- Public -------------------------------------------------------------

    def apply_startup(self):
        if self.cfg.get("enabled_on_start", False):
            self.toggle.select()
            self._toggle()

    # ---- Internals ----------------------------------------------------------

    def _clear_label_image(self):
        """Forcefully remove any Tk image reference from the label."""
        try:
            self._ctk_img = None
            # Clear via CTk API
            self.lbl.configure(image=None)
            # Also clear underlying Tk image binding just in case
            try:
                self.lbl._label.configure(image="")  # safe no-op if not present
            except Exception:
                pass
        except Exception:
            pass

    def _toggle(self):
        if self.toggle.get():
            # Turn ON
            self._img_gen += 1
            self._start_ts = time.time()

            # IMPORTANT: clear old image BEFORE setting text to avoid "pyimage… doesn't exist"
            self._clear_label_image()
            self.lbl.configure(text="Starting...")

            self.worker = CameraWorker(
                index=int(self.cfg["index"]),
                width=int(self.cfg.get("width", 640)),
                height=int(self.cfg.get("height", 480)),
                target_fps=int(self.cfg.get("target_fps", 15)),
                on_frame=self._on_frame,
                name=self.name,
                backend=self.cfg.get("backend", "auto"),  # "auto" tries DSHOW -> MSMF
            )
            self.worker.start()

            def verify_open():
                # widget still alive / still ON?
                if not self.winfo_exists() or not self.toggle.get() or self.worker is None:
                    return
                if self.worker.is_opened():
                    # Opened successfully
                    if self.bus and getattr(self.worker, "actual_backend", None):
                        self.bus.publish(
                            "log:line",
                            f"[{self.name}] opened via {self.worker.actual_backend.upper()} idx={self.cfg['index']}",
                        )
                    self.lbl.configure(text="")
                    return

                # keep waiting up to 6s
                if time.time() - (self._start_ts or 0) < 6.0:
                    self.after(150, verify_open)
                    return

                # Timed out -> turn OFF cleanly
                try:
                    if self.worker:
                        self.worker.stop()
                finally:
                    self.worker = None
                self.toggle.deselect()
                self._clear_label_image()
                self.lbl.configure(text=f"{self.name} (OFF)")
                if self.bus:
                    self.bus.publish("log:line", f"[{self.name}] Camera not available (timeout opening)")

            self.after(150, verify_open)

        else:
            # Turn OFF
            self._img_gen += 1
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
            # Clear image FIRST, then set text
            self._clear_label_image()
            self.lbl.configure(text=f"{self.name} (OFF)")
            self._start_ts = None

    def _rec_toggle(self):
        self.recording = bool(self.rec_btn.get())
        if self.recording and self.worker and self.worker.last_frame is not None:
            folder = self._rec_folder()
            os.makedirs(folder, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            codec = cv2.VideoWriter_fourcc(*"mp4v")
            h, w = self.worker.last_frame.shape[:2]
            out_path = os.path.join(folder, f"{self.name}_{ts}.mp4")
            self.out = cv2.VideoWriter(out_path, codec, 20, (w, h))
            if not self.out.isOpened():
                if self.bus:
                    self.bus.publish("log:line", f"[{self.name}] ERROR: failed to open VideoWriter")
                self.rec_btn.deselect()
                self.recording = False
                self.out = None
            else:
                if self.bus:
                    self.bus.publish("log:line", f"[{self.name}] Recording -> {out_path}")
        else:
            if self.out:
                try:
                    self.out.release()
                finally:
                    self.out = None
            if self.bus and self.recording is False:
                self.bus.publish("log:line", f"[{self.name}] Recording stopped")

    def snapshot(self):
        if self.worker and self.worker.last_frame_bgr is not None:
            folder = self._rec_folder()
            os.makedirs(folder, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            path = os.path.join(folder, f"{self.name}_{ts}.png")
            try:
                cv2.imwrite(path, self.worker.last_frame_bgr)
                if self.bus:
                    self.bus.publish("log:line", f"[{self.name}] Snapshot saved: {path}")
            except Exception as e:
                if self.bus:
                    self.bus.publish("log:line", f"[{self.name}] Snapshot error: {e}")
        else:
            if self.bus:
                self.bus.publish("log:line", f"[{self.name}] Snapshot skipped (no frame)")

    def _rec_folder(self):
        # Try to read from parent config (optional), else default
        try:
            return self.master.master.cfg["cameras"]["recording"]["folder"]
        except Exception:
            return "captures"

    def _on_frame(self, frame_bgr):
        """Worker thread callback → schedule a main-thread UI update using CTkImage."""
        gen = self._img_gen
        frame_copy = frame_bgr.copy()

        def _apply():
            if not self.winfo_exists():
                return
            if gen != self._img_gen:
                return
            if not self.toggle.get() or self.worker is None:
                return
            try:
                rgb = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)
                # Use CTkImage to avoid High-DPI warnings and keep a strong reference
                self._ctk_img = ctk.CTkImage(light_image=pil_img, size=(640, 480))
                self.lbl.configure(image=self._ctk_img, text="")
            except Exception as e:
                if self.bus:
                    self.bus.publish("log:line", f"[{self.name}] UI apply err: {e}")

            if self.recording and self.out is not None:
                try:
                    self.out.write(frame_copy)
                except Exception as e:
                    if self.bus:
                        self.bus.publish("log:line", f"[{self.name}] record err: {e}")

        self.after(0, _apply)


class DualCameraPanel(ctk.CTkFrame):
    def __init__(self, master, cameras_cfg, bus):
        super().__init__(master)
        self.cfg = getattr(master, "cfg", {})  # optional: for recording folder

        idx_a = cameras_cfg["cam_a"]["index"]
        idx_b = cameras_cfg["cam_b"]["index"]
        if idx_a == idx_b and bus:
            bus.publish("log:line", f"[Cameras] ERROR: CamA and CamB share the same index ({idx_a}). Fix YAML.")

        self.cam_a = CamTile(self, "CamA", cameras_cfg["cam_a"], bus)
        self.cam_b = CamTile(self, "CamB", cameras_cfg["cam_b"], bus)

        self.cam_a.grid(row=0, column=0, padx=6, pady=6, sticky="n")
        self.cam_b.grid(row=0, column=1, padx=6, pady=6, sticky="n")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def apply_startup(self):
        # Stagger to avoid driver/backend races
        self.cam_a.apply_startup()
        self.after(600, self.cam_b.apply_startup)
