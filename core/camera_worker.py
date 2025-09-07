# OpenCV camera worker
import cv2, threading, time

class CameraWorker:
    def __init__(self, index=0, width=640, height=480, target_fps=20, on_frame=None):
        self.idx, self.size = index, (width, height)
        self.fps = target_fps
        self.on_frame = on_frame
        self.cap = None
        self.stop = threading.Event()
        self.last_frame = None
        self.last_frame_bgr = None

    def start(self):
        # Prefer DirectShow on Windows to avoid long blocking opens
        try:
            self.cap = cv2.VideoCapture(self.idx, cv2.CAP_DSHOW)
        except Exception:
            self.cap = cv2.VideoCapture(self.idx)

        # Small buffer & size caps help reduce latency
        try: self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception: pass
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])
        # Some drivers accept a target FPS hint
        try: self.cap.set(cv2.CAP_PROP_FPS, float(self.fps))
        except Exception: pass

        # Open timeout (≈1s): if not opened, bail out cleanly
        import time
        t0 = time.time()
        while not self.cap.isOpened() and (time.time() - t0) < 1.0:
            time.sleep(0.05)
        if not self.cap.isOpened():
            # publish a log line if you want:
            if self.on_frame is not None:
                # optional: signal failure upstream by sending None
                pass
            try: self.cap.release()
            except Exception: pass
            self.cap = None
            return

        threading.Thread(target=self._loop, daemon=True).start()


    def stop(self):
        self.stop.set()
        if self.cap:
            try: self.cap.release()
            except: pass
        self.cap = None

    def _loop(self):
        delay = max(1.0/self.fps, 0.02)
        bad = 0
        while not self.stop.is_set() and self.cap and self.cap.isOpened():
            ok, frame = self.cap.read()
            if ok and frame is not None:
                bad = 0
                self.last_frame_bgr = frame
                self.last_frame = frame
                if self.on_frame:
                    self.on_frame(frame)
            else:
                bad += 1
                if bad >= 30:   # ~1.5s at 20fps
                    break
            time.sleep(delay)
        # cleanup
        try: self.cap.release()
        except Exception: pass
        self.cap = None

