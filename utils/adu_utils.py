import os
from ctypes import WinDLL
from utils.adu_python_dll.ontrak.aduhid import (
    open_device_by_product_id,
    close_device,
    write_device as adu_write,
)

# Constants
PRODUCT_ID = 222  # Your ADU's Product ID
TIMEOUT = 5000


def get_dll_path():
    """
    Returns the absolute path to the ADU DLL file, dynamically resolved.
    This avoids hardcoded paths and supports relative project structure.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))  # Go one level up from utils/
    dll_path = os.path.join(base_dir, "utils", "adu_python_dll", "ontrak", "AduHid64.dll")
    return dll_path


def open_adu_device():
    """
    Attempts to load the ADU DLL and open the device by product ID.
    Returns the device handle or None if not found.
    """
    dll_path = get_dll_path()
    print(f"[DEBUG] Loading ADU DLL from: {dll_path}")
    WinDLL(dll_path)  # Load globally for DLL dependency
    return open_device_by_product_id(PRODUCT_ID, TIMEOUT)


def close_adu_device(device):
    """
    Closes the ADU device handle cleanly if it's open.
    """
    if device:
        close_device(device)
        print("[DEBUG] ADU device closed.")


def write_device(device, command):
    """
    Sends a command to the ADU device.
    :param device: handle returned by open_adu_device()
    :param command: string like 'sk1', 'rk1', etc.
    """
    if device:
        print(f"[DEBUG] Writing to ADU: {command}")
        adu_write(device, command, TIMEOUT)
