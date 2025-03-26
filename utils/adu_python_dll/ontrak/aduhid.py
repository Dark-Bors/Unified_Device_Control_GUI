# Wrapper for OnTrak Control Systems' AduHid.dll (USB/Device Pipe Functions)
# See: https://www.ontrak.net/ADUSDK/Functions.html

from ctypes import *
from ctypes.wintypes import *
import platform
import os

ontrak_vendor_id = 0x0A07
INVALID_HANDLE_VALUE = c_void_p(-1).value

class ADU_DEVICE_ID(Structure):
	_fields_ = [
		("vendor_id", c_ushort),
		("product_id", c_ushort),
		("serial_number", c_char * 7)
	]

# dll_path = os.path.dirname(__file__)
# Full path to the DLL
dll_path = r"C:\Boris_Tests\Tools\adu_python_dll\ontrak\AduHid64.dll"
print("path to dll:", dll_path)
os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']
arch = platform.architecture()
if arch[0] == '32bit':
	adu_lib = WinDLL('AduHid')
elif arch[0] == '64bit':
	adu_lib = WinDLL(dll_path)

_adu_count = adu_lib.ADUCount
_adu_count.restype = c_int
_adu_count.argtypes = [c_ulong]

_show_adu_device_list = adu_lib.ShowAduDeviceList
_show_adu_device_list.restype = None
_show_adu_device_list.argtypes = [POINTER(ADU_DEVICE_ID), c_char_p]

_get_adu_device_list = adu_lib.GetAduDeviceList
_get_adu_device_list.restype = None
_get_adu_device_list.argtypes = [POINTER(ADU_DEVICE_ID), c_ushort, c_ulong, POINTER(c_ushort), POINTER(BOOL)]

_open_adu_device = adu_lib.OpenAduDevice
_open_adu_device.restype = POINTER(HANDLE)
_open_adu_device.argtypes = [c_ulong]

_open_adu_device_by_product_id = adu_lib.OpenAduDeviceByProductId
_open_adu_device_by_product_id.restype = POINTER(HANDLE)
_open_adu_device_by_product_id.argtypes = [c_int, c_ulong]

_open_adu_device_by_serial_number = adu_lib.OpenAduDeviceBySerialNumber
_open_adu_device_by_serial_number.restype = POINTER(HANDLE)
_open_adu_device_by_serial_number.argtypes = [c_char_p, c_ulong]

_close_adu_device = adu_lib.CloseAduDevice
_close_adu_device.restype = None
_close_adu_device.argtypes = [POINTER(HANDLE)]

_write_adu_device = adu_lib.WriteAduDevice
_write_adu_device.restype = c_int
_write_adu_device.argtypes = [POINTER(HANDLE), c_char_p, c_ulong, POINTER(c_ulong), c_ulong]

_read_adu_device = adu_lib.ReadAduDevice
_read_adu_device.restype = c_int
_read_adu_device.argtypes = [POINTER(HANDLE), c_char_p, c_ulong, POINTER(c_ulong), c_ulong]

adu_handle_type = POINTER(HANDLE)

def ValidHandle(handle):
	cast_handle = cast(handle, HANDLE)
	return (cast_handle.value != 0 and cast_handle.value != INVALID_HANDLE_VALUE)

# Get the number of connected ADU devices
# Returns number of connected devices
def count(timeout):
	return _adu_count(timeout)

# Get a list connected ADU devices. Allows access to vendor_id, product_id, and serial_number of each device
# See documentation link at top of page for explanation of timeout 
# Returns a list of ADU_DEVICE_ID structures
def device_list(timeout):
	num_adus = _adu_count(timeout)
	device_list = (ADU_DEVICE_ID * num_adus)()
	num_devices_found = c_ushort()
	result = BOOL()
	_get_adu_device_list(device_list, num_adus, timeout, byref(num_devices_found), byref(result))
	return device_list

# Display a Windows GUI popup with a list of ADU devices, allowing selection of one.
# Returns the selected ADU_DEVICE_ID object which that then be used to open the device via a serial number or product id.
# Returns None if no device was selecte from list
def show_device_list(header_string):
	device_id = ADU_DEVICE_ID()
	_show_adu_device_list(device_id, c_char_p(header_string.encode()))

	if device_id.product_id == 0x00 and device_id.vendor_id == 0x00:
		return None

	return device_id

# Searches for any ADU device attached to the computer. See documentation link at top of page for explanation of timeout 
# The function opens the first ADU device that it encounters and passes back a handle to it. 
# Returns a device handle on success, and None on failure
def open_adu_device(timeout):
	device_handle = _open_adu_device(timeout)
	if not ValidHandle(device_handle):
		return None

	return device_handle

# Open an ADU device by product ID. See documentation link at top of page for explanation of timeout 
# Returns a device handle on success, and None on failure
def open_device_by_product_id(product_id, timeout):
	device_handle = _open_adu_device_by_product_id(product_id, timeout)
	if not ValidHandle(device_handle):
		return None

	return device_handle

# Open an ADU device by serial number. See documentation link at top of page for explanation of timeout 
# Returns a device handle on success, and None on failure
def open_device_by_serial_number(serial_number, timeout):
	device_handle = _open_adu_device_by_serial_number(serial_number, timeout)
	if False == ValidHandle(device_handle):
		return None

	return device_handle
	
# Close a connected ADU device
def close_device(device_handle):
	_close_adu_device(device_handle)

# Write a command to the device. The command is an ASCII string representing the command, such as 'SK0'
# Returns 0 if failed, other value if successful
def write_device(device_handle, command, timeout):
	bytes_written = c_ulong()
	result = _write_adu_device(device_handle, c_char_p(command.encode()), len(command), byref(bytes_written), timeout)
	return result
	
# Read a pending value from the device. Data will be pending if a responsive command was previously issued (such as 'RPK0')
# Returns the result of the read (0 if successul, other value if failure). Value will contain the read value as a string on success, and None on failure
def read_device(device_handle, timeout):
	read_string = b'#' * 7
	read_buffer = c_char_p(read_string)
	bytes_read = c_ulong()
	result = _read_adu_device(device_handle, read_buffer, 7, byref(bytes_read), timeout)

	if result == 0: # unsuccessful read
		return (result, None)

	return (result, read_string.decode().rstrip('\x00'))