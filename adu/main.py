from ontrak import aduhid

PRODUCT_ID = 222 # Set the product id to match your ADU device. See list here: https://www.ontrak.net/Nodll.htm

# Example of getting the number of connected ADU devices
#num_adu = aduhid.count(100)
#print('Number of ADU devices connected: %i' % (num_adu))
#
#device_list = aduhid.device_list(100)
#for device in device_list:
#	print('Vendor ID: %i, Product ID: %i, Serial Number: %s' % (device.vendor_id, device.product_id, device.serial_number))

# open device by product id
device_handle = aduhid.open_device_by_product_id(PRODUCT_ID, 100)
if device_handle == None:
	print('Error opening device. Ensure that the product id is correct and that it is connected')
	exit(-1)

# Write a command to the device
result = aduhid.write_device(device_handle, 'RK0', 100)
print('Write result: %i' % result) # Should be non-zero if successful

result = aduhid.write_device(device_handle, 'SK0', 100)
print('Write result: %i' % result) # Should be non-zero if successful

result = aduhid.write_device(device_handle, 'RPA', 100)
print('Write result: %i' % result) # Should be non-zero if successful

# Read from device
(result, value) = aduhid.read_device(device_handle, 100)	

# Result will contain the returned value from the device in integer form 
# If read is not successful, result is 0 and value is None
if result != 0:
	print('Read result: %i, value: %s' % (result, value)) 
else:
	print('Read failed - was a resulting command issued prior to the read?') 

aduhid.close_device(device_handle)
