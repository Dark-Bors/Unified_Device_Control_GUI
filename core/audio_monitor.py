# core/audio_monitor.py
import threading
import sounddevice as sd


class AudioMonitor:
    """
    Low-latency loopback: microphone -> speakers (no recording).
    Creates a full-duplex Stream and copies the input buffer to the output buffer.
    """

    def __init__(self, logger=None, input_hint=None, samplerate=48000, channels=1, blocksize=1024):
        self.log = logger or (lambda *a, **k: None)
        self.input_hint = input_hint
        self.samplerate = int(samplerate)
        self.channels = int(channels)
        self.blocksize = int(blocksize)

        self._stream = None
        self._lock = threading.Lock()
        self._input_dev = None
        self._output_dev = None

    @staticmethod
    def _find_device_by_hint(hint, kind="input"):
        """Return device index whose name contains `hint` (case-insensitive), else None."""
        if not hint:
            return None
        hint = hint.lower()
        try:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                name = str(dev.get("name", "")).lower()
                max_in = int(dev.get("max_input_channels", 0))
                max_out = int(dev.get("max_output_channels", 0))
                if hint in name:
                    if kind == "input" and max_in > 0:
                        return idx
                    if kind == "output" and max_out > 0:
                        return idx
        except Exception:
            pass
        return None

    def _select_devices(self):
        """Pick input by hint (if available), output = system default speakers."""
        try:
            defaults = sd.default
            dev_in = self._find_device_by_hint(self.input_hint, kind="input")
            if dev_in is None:
                dev_in = defaults.device[0]  # default input
            dev_out = defaults.device[1]     # default output
            self._input_dev = dev_in
            self._output_dev = dev_out

            # Log selection
            dinfo = sd.query_devices(self._input_dev) if self._input_dev is not None else {}
            dout = sd.query_devices(self._output_dev) if self._output_dev is not None else {}
            self.log(f"[AUDIO] input={dinfo.get('name','?')} (idx={self._input_dev}), "
                     f"output={dout.get('name','?')} (idx={self._output_dev})")
        except Exception as e:
            self.log(f"[AUDIO] device selection failed: {e}")
            self._input_dev = None
            self._output_dev = None

    def _callback(self, indata, outdata, frames, time_info, status):
        if status:
            # Non-fatal over/underruns; could log if needed
            pass
        # Copy mic input to speakers (supports mono or multi-channel)
        outdata[:] = indata

    def start(self):
        with self._lock:
            if self._stream is not None:
                return
            self._select_devices()
            try:
                self._stream = sd.Stream(
                    samplerate=self.samplerate,
                    blocksize=self.blocksize,
                    dtype="float32",
                    channels=self.channels,
                    callback=self._callback,
                    device=(self._input_dev, self._output_dev),
                )
                self._stream.start()
                self.log("[AUDIO] monitor started")
            except Exception as e:
                self.log(f"[AUDIO] start failed: {e}")
                self._stream = None

    def stop(self):
        with self._lock:
            if self._stream is None:
                return
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                self.log(f"[AUDIO] stop error: {e}")
            finally:
                self._stream = None
                self.log("[AUDIO] monitor stopped")

    def is_running(self):
        s = self._stream
        return bool(s and s.active)
