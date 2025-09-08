# core/adu_client.py
import os
import sys
from ctypes import WinDLL
from typing import Optional

from adu.ontrak import aduhid   # this matches your old working code:contentReference[oaicite:4]{index=4}

APP_TAG = "<UDC app>"
ADU_TAG = "<ADU>"

_DEFAULT_ACTION_MAP = {
    "USB_ON":   "SK3",
    "USB_OFF":  "RK3",
    "LIGHT_ON": "SK1",
    "LIGHT_OFF":"RK1",
}

class ADUClient:
    """
    Ontrak ADU wrapper using ontrak.aduhid and AduHid.dll/AduHid64.dll.
    """

    def __init__(self, bus, product_id: int = 218,
                 dll_dir: Optional[str] = None,
                 action_map: Optional[dict] = None,
                 timeout_ms: int = 5000,
                 serial: Optional[str] = None):
        self.bus = bus
        self.product_id = int(product_id)
        self.serial = serial
        self.timeout = int(timeout_ms)
        self.dll_dir = dll_dir
        self.action_map = action_map or _DEFAULT_ACTION_MAP

        self._handle = None

        # Make sure DLL is loaded globally, same as adu_utils.py:contentReference[oaicite:5]{index=5}
        if self.dll_dir:
            dll_path = os.path.join(self.dll_dir, "AduHid64.dll")
            if os.path.exists(dll_path):
                WinDLL(dll_path)

    # ---------- logging ----------
    def _log_app(self, msg): self.bus.publish("log:line", f"{APP_TAG} {msg}")
    def _log_adu(self, msg): self.bus.publish("log:line", f"{ADU_TAG} {msg}")

    # ---------- lifecycle ----------
    def connect(self) -> bool:
        try:
            self._handle = aduhid.open_device_by_product_id(self.product_id, self.timeout)
            if not self._handle:
                self._log_app(f"ADU connect failed (product_id={self.product_id})")
                return False
            self._log_app(f"ADU connected (product_id={self.product_id})")
            return True
        except Exception as e:
            self._log_app(f"ADU connect error: {e}")
            return False

    def disconnect(self):
        try:
            if self._handle:
                aduhid.close_device(self._handle)
                self._log_app("ADU disconnected.")
        except Exception:
            pass
        finally:
            self._handle = None

    def is_connected(self) -> bool:
        return self._handle is not None

    # ---------- I/O ----------
    def write(self, cmd: str) -> bool:
        if not self._handle:
            self._log_app("ADU write failed: not connected.")
            return False
        try:
            res = aduhid.write_device(self._handle, cmd, self.timeout)
            ok = bool(res)
            self._log_adu(f"TX {cmd} -> {'OK' if ok else 'FAIL'}")
            return ok
        except Exception as e:
            self._log_app(f"ADU write error: {e}")
            return False

    # ---------- high-level ----------
    def action(self, name: str) -> bool:
        cmd = self.action_map.get(name)
        if not cmd:
            self._log_app(f"ADU unknown action: {name}")
            return False
        return self.write(cmd)
