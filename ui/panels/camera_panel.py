# ui/panels/camera_panel.py
# Dual camera panel (CTkImage updates on main thread, robust toggles, safe image clearing)

import os
import time
import cv2
import customtkinter as ctk
from PIL import Image

from core.camera_worker import CameraWorker
from core.audio_monitor import AudioMonitor


class CamTile(ctk.CTkFrame):
    def __init__(self, master, name, cfg, bus, app_cfg):
        """
        master: parent widget
        name: "CamA" / "CamB"
        cfg: camera config dict for this tile
        bus: pubsub/logger bus with topic 'log:line' (or None)
        app_cfg: full YAML config (used for audio + recording folder)
        """
        super().__init__(master)
        self.name, self.cfg, self.bus = name, cfg, bus
        self.app_cfg = app_cfg

        # Simple logger hook
        def _noop(*a, **k): ...
        self._log = lambda msg: (self.bus.publish("log:line", msg) if self.bus else _noop(msg))

        # --- Display ---
        self.lbl = ctk.CTkLabel(self, text=f"{name} (OFF)", width=640, height=480)
        self.lbl.pack(padx=6, pady=6)

        # --- Controls row (use PACK; don't mix with GRID on same parent) ---
        controls = ctk.CTkFrame(self)
        controls.pack(pady=(0, 6))

        self.toggle = ctk.CTkSwitch(controls, text=f"{name} ON", command=self._toggle)
        self.toggle.pack(side="left", padx=6)

        self.snap_btn = ctk.CTkButton(controls, text="Snapshot", command=self.snapshot)
        self.snap_btn.pack(side="left", padx=6)

        self.rec_btn = ctk.CTkSwitch(controls, text="Record", command=self._rec_toggle)
        self.rec_btn.pack(side="left", padx=6)

        # --- Audio monitor ---
        a_cfg = (app_cfg.get("audio") or {})
        self.audio_monitor = AudioMonitor(
            logger=self._log,
            input_hint=a_cfg.get("input_hint"),
            samplerate=int(a_cfg.get("samplerate", 48000)),
            channels=int(a_cfg.get("channels", 1)),
            blocksize=int(a_cfg.get("blocksize", 1024)),
        )

        self.mic_btn = ctk.CTkButton(controls, text="🔇 MIC OFF", width=120, command=self._toggle_mic)
        self.mic_btn.pack(side="left", padx=6)

        if a_cfg.get("autostart_monitor"):
            self.after(300, self._toggle_mic)

        # --- State ---
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
            self.lbl.configure(image=None)
            try:
                # underlying Tk label; if available, clear its image too
                self.lbl._label.configure(image="")
            except Exception:
                pass
        except Exception:
            pass

    def _toggle(self):
        if self.toggle.get():
            # Turn ON
            self._img_gen += 1
            self._start_ts = time.time()
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
                if not self.winfo_exists() or not self.toggle.get() or self.worker is None:
                    return
                if self.worker.is_opened():
                    if self.bus and getattr(self.worker, "actual_backend", None):
                        self.bus.publish(
                            "log:line",
                            f"[{self.name}] opened via {self.worker.actual_backend.upper()} idx={self.cfg['index']}",
                        )
                    self.lbl.configure(text="")
                    return

                # wait up to 6s
                if time.time() - (self._start_ts or 0) < 6.0:
                    self.after(150, verify_open)
                    return

                # timeout -> turn OFF
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
                self._log(f"[{self.name}] ERROR: failed to open VideoWriter")
                self.rec_btn.deselect()
                self.recording = False
                self.out = None
            else:
                self._log(f"[{self.name}] Recording -> {out_path}")
        else:
            if self.out:
                try:
                    self.out.release()
                finally:
                    self.out = None
            if self.recording is False:
                self._log(f"[{self.name}] Recording stopped")

    def snapshot(self):
        if self.worker and getattr(self.worker, "last_frame_bgr", None) is not None:
            folder = self._rec_folder()
            os.makedirs(folder, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            path = os.path.join(folder, f"{self.name}_{ts}.png")
            try:
                cv2.imwrite(path, self.worker.last_frame_bgr)
                self._log(f"[{self.name}] Snapshot saved: {path}")
            except Exception as e:
                self._log(f"[{self.name}] Snapshot error: {e}")
        else:
            self._log(f"[{self.name}] Snapshot skipped (no frame)")

    def _toggle_mic(self):
        try:
            if self.audio_monitor.is_running():
                self.audio_monitor.stop()
                self.mic_btn.configure(text="🔇 MIC OFF")
            else:
                self.audio_monitor.start()
                self.mic_btn.configure(text="🔊 MIC ON" if self.audio_monitor.is_running() else "🔇 MIC OFF")
        except Exception as e:
            self._log(f"[AUDIO] toggle error: {e}")

    def _rec_folder(self):
        try:
            return self.app_cfg["cameras"]["recording"]["folder"]
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
                self._ctk_img = ctk.CTkImage(light_image=pil_img, size=(640, 480))
                self.lbl.configure(image=self._ctk_img, text="")
            except Exception as e:
                self._log(f"[{self.name}] UI apply err: {e}")

            if self.recording and self.out is not None:
                try:
                    self.out.write(frame_copy)
                except Exception as e:
                    self._log(f"[{self.name}] record err: {e}")

        self.after(0, _apply)


class DualCameraPanel(ctk.CTkFrame):
    def __init__(self, master, cameras_cfg, bus):
        super().__init__(master)
        # Expect MainWindow to have full YAML config on .cfg
        self.cfg = getattr(master, "cfg", {})

        idx_a = cameras_cfg["cam_a"]["index"]
        idx_b = cameras_cfg["cam_b"]["index"]
        if idx_a == idx_b and bus:
            bus.publish("log:line", f"[Cameras] ERROR: CamA and CamB share the same index ({idx_a}). Fix YAML.")

        # Pass app_cfg to tiles
        self.cam_a = CamTile(self, "CamA", cameras_cfg["cam_a"], bus, self.cfg)
        self.cam_b = CamTile(self, "CamB", cameras_cfg["cam_b"], bus, self.cfg)

        self.cam_a.grid(row=0, column=0, padx=6, pady=6, sticky="n")
        self.cam_b.grid(row=0, column=1, padx=6, pady=6, sticky="n")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def apply_startup(self):
        # Stagger to avoid driver/backend races
        self.cam_a.apply_startup()
        self.after(600, self.cam_b.apply_startup)
