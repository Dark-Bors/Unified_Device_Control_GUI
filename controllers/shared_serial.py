import serial
import serial.tools.list_ports
import time


def get_shared_serial_connection():
    ports = serial.tools.list_ports.comports()
    ports.sort(key=lambda port: int(port.device.lstrip("COM")))
    for port in ports:
        try:
            ser = serial.Serial(port.device, 9600, timeout=1)
            time.sleep(2)
            ser.write(b"PING\n")
            time.sleep(0.5)
            if "PONG" in ser.read(100).decode():
                print(f"Shared Serial Connected to {port.device}")
                return ser
            ser.close()
        except Exception as e:
            print(f"Shared Serial: Failed on {port.device}: {e}")
    return None
