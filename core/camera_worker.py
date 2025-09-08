# core/camera_worker.py
# Threaded OpenCV worker (auto backend fallback, DirectShow/MSMF, MJPG, serialized open)

import cv2, threading, time, traceback

class CameraWorker:
    _OPEN_LOCK = threading.Lock()  # serialize opens to avoid same-device races

    def __init__(self, index=0, width=640, height=480, target_fps=15,
                 on_frame=None, name="cam", backend="auto"):
        self.idx = int(index)
        self.w, self.h = int(width), int(height)
        self.fps  = float(target_fps) if target_fps else 15.0
        self.on_frame = on_frame
        self.name = name
        self.backend = (backend or "auto").lower()  # "auto" | "dshow" | "msmf"

        self.cap = None
        self._thread = None
        self._stop_event = threading.Event()
        self._opened = threading.Event()   # set after first good frame

        self.last_frame = None
        self.last_frame_bgr = None

        # set by _open_capture() to tell caller which backend actually succeeded
        self.actual_backend = None  # "dshow" | "msmf" | None

    # ---------- public ----------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._opened.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def is_opened(self):
        return self._opened.is_set()

    # ---------- internals ----------
    def _run(self):
        try:
            if not self._open_capture():
                return

            delay = max(1.0 / self.fps, 0.02)
            bad = 0
            got_first = False
            t0 = time.time()

            while not self._stop_event.is_set() and self.cap and self.cap.isOpened():
                ok, frame = self.cap.read()
                if ok and frame is not None:
                    bad = 0
                    self.last_frame_bgr = frame
                    self.last_frame = frame

                    if not got_first:
                        got_first = True
                        self._opened.set()

                    if self.on_frame:
                        try:
                            self.on_frame(frame)
                        except Exception:
                            traceback.print_exc()
                else:
                    bad += 1
                    if bad >= 30:
                        if not self._opened.is_set() and (time.time() - t0) > 3.0:
                            break
                        bad = 0
                time.sleep(delay)
        finally:
            try:
                if self.cap:
                    self.cap.release()
            except Exception:
                pass
            self.cap = None

    def _configure(self, cap):
        # Force MJPG + small buffer + size/fps
        try: cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        except Exception: pass
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)
            cap.set(cv2.CAP_PROP_FPS, float(self.fps))
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

    def _try_backend(self, be_flag, be_name):
        """Attempt to open with backend flag; return cap or None."""
        cap = cv2.VideoCapture(self.idx, be_flag)
        t0 = time.time()
        while not cap.isOpened() and time.time() - t0 < 2.0:
            time.sleep(0.05)
        if not cap.isOpened():
            try: cap.release()
            except Exception: pass
            return None

        self._configure(cap)
        # warm-up: ensure we can actually read
        ok = False
        for _ in range(8):
            ok, _frm = cap.read()
            if ok:
                break
            time.sleep(0.05)
        if not ok:
            try: cap.release()
            except Exception: pass
            return None

        self.actual_backend = be_name
        return cap

    def _open_capture(self):
        """Open camera with preferred backend(s); serialize to avoid simultaneous grabs."""
        order = []
        if self.backend == "dshow":
            order = [("dshow", cv2.CAP_DSHOW)]
        elif self.backend == "msmf":
            order = [("msmf", cv2.CAP_MSMF)]
        else:
            # AUTO: try DSHOW first (good with MJPG), then MSMF
            order = [("dshow", cv2.CAP_DSHOW), ("msmf", cv2.CAP_MSMF)]

        with self._OPEN_LOCK:
            for be_name, be_flag in order:
                cap = self._try_backend(be_flag, be_name)
                if cap is not None:
                    self.cap = cap
                    return True

        self.cap = None
        return False
