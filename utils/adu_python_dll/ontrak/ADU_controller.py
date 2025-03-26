import tkinter as tk
from tkinter import ttk
import aduhid

# Initialize the device
timeout = 5000  # Set an appropriate timeout
device_handle = aduhid.open_adu_device(timeout)

if device_handle is None:
    print("Failed to open device.")
else:
    print("Device opened successfully.")

# Define the command functions
def power_on():
    if device_handle:
        result = aduhid.write_device(device_handle, 'sk0', timeout)
        if result == 0:
            print("Failed to send Power On command.")
        else:
            print("Power On command sent successfully.")

def power_off():
    if device_handle:
        result = aduhid.write_device(device_handle, 'rk0', timeout)
        if result == 0:
            print("Failed to send Power Off command.")
        else:
            print("Power Off command sent successfully.")

def usb_on():
    if device_handle:
        result = aduhid.write_device(device_handle, 'sk1', timeout)
        if result == 0:
            print("Failed to send USB On command.")
        else:
            print("USB On command sent successfully.")

def usb_off():
    if device_handle:
        result = aduhid.write_device(device_handle, 'rk1', timeout)
        if result == 0:
            print("Failed to send USB Off command.")
        else:
            print("USB Off command sent successfully.")

# Create the main application window
root = tk.Tk()
root.title("Device Control")

# Set the dark theme colors
bg_color = '#2e2e2e'  # Dark gray
fg_color = '#262626'  # Light gray
button_color = '#333333'  # Darker gray
highlight_color = '#3e3e3e'  # Slightly lighter gray for button highlight

root.configure(bg=bg_color)

# Apply the theme to buttons
style = ttk.Style()
style.configure('TButton', background=button_color, foreground=fg_color, 
                borderwidth=1, focusthickness=3, focuscolor=highlight_color,
                relief='flat')
style.map('TButton', background=[('active', highlight_color)])

# Create and place the buttons
button_frame = tk.Frame(root, bg=bg_color)
button_frame.pack(pady=20, padx=20)

power_on_button = ttk.Button(button_frame, text="Power On", command=power_on, style='TButton')
power_on_button.grid(row=0, column=0, padx=10, pady=10)

power_off_button = ttk.Button(button_frame, text="Power Off", command=power_off, style='TButton')
power_off_button.grid(row=0, column=1, padx=10, pady=10)

usb_on_button = ttk.Button(button_frame, text="USB On", command=usb_on, style='TButton')
usb_on_button.grid(row=1, column=0, padx=10, pady=10)

usb_off_button = ttk.Button(button_frame, text="USB Off", command=usb_off, style='TButton')
usb_off_button.grid(row=1, column=1, padx=10, pady=10)

# Start the GUI event loop
root.mainloop()

# Close the device handle when the application is closed
if device_handle:
    aduhid.close_device(device_handle)
    print("Device closed successfully.")
