# Unified Device Control GUI

**Version:** 0.3.0  

**Author:** Dark Bors =]

**License:** MIT

**Platform:** Windows (due to ADU DLL dependency)

A Python-based GUI for controlling and automating multiple lab devices from a single interface. Supports camera modules, ADU USB relays, servo motors, and magnet drivers — with real-time feedback, shared serial communication, and robust error handling.

---

## 🚀 Features

- 🎛️ Unified control panel for multiple device types
- 🔁 Shared serial port connection across modules
- 📷 Real-time USB camera streaming
- 🧲 Magnet relay control (ON/OFF)
- ⚙️ Servo motor automation with timer cycles
- 🔌 ADU USB relay control (Power + USB switching)
- ✅ Connection and status indicators per device
- 🧪 Supports simulation/testing without hardware
- 🪵 Logging, debug prints, and modular structure for future extensions (e.g., MQTT, S3)

---

## 🧭 GUI Layout Overview

> _Add real screenshots in the `/assets/img/` folder and reference them here._  
> Example:  
> `![Dashboard Screenshot](assets/img/dashboard.png)`

---

## 🧱 Project Structure

```
main.py
│
├── gui/
│   ├── gui_main.py
│   ├── camera_gui.py
│   ├── magnet_gui.py
│   ├── servo_gui.py
│   └── adu_gui.py
│
├── controllers/
│   └── shared_serial.py
│
├── utils/
│   └── adu_python_dll/
│
├── adu_utils.py
├── version.py
├── requirements.txt
└── README.md
```

---

## 🛠️ Installation

### Clone the repository:

```
git clone https://github.com/Dark-Bors/Unified_Device_Control_GUI.git
cd Unified_Device_Control_GUI
```

### Create a virtual environment (recommended):

```
python -m venv venv
venv\Scripts\activate   # For Windows
```

### Install dependencies:

```
pip install -r requirements.txt
```

### Run the application:

```
python main.py
```

---

## 📦 Requirements

- Windows OS (for ADU DLL support)
- Python 3.8+
- USB Camera (external)
- Ontrak ADU USB Relay (e.g., ADU200 series)

### Python Libraries

```
customtkinter>=5.2.0
opencv-python
Pillow
pyserial
```

---

## 🔌 Device Modules

### 🧲 Magnet Control

- Toggle ON/OFF via serial: `ON`, `OFF`
- Displays connection status

### ⚙️ Servo Control

- Manual clockwise/counter-clockwise movement
- Automated ON/OFF cycles (up to 4680)
- Built-in STOP safeguard
- Live timer feedback label

### 🔌 ADU USB Relay

- Uses `AduHid64.dll` via `ctypes.WinDLL`
- Commands: `sk0`, `sk1`, `rk0`, `rk1`
- Displays device connection status

### 📷 Camera Viewer

- Live stream from USB camera using OpenCV
- Camera index set to `1`
- Scales and updates frames in real-time

---

## 🔁 Serial Port Sharing

- Auto-detects connected COM ports
- Sends `PING` and waits for `PONG`
- Shared instance across Servo and Magnet modules

---

## 🧪 Testing and Sim Mode

- Runs even without devices connected
- Uses threading for responsive GUI
- Mock serial class can be used for offline simulation

---

## 💡 Future Enhancements

- MQTT-based control and logging
- AWS S3 integration for data uploads
- GUI-based field-to-command mapping system
- Per-device configuration persistence

---

## 🧯 Error Handling

All modules handle and report:

- Device not connected
- Serial port communication errors
- DLL loading issues
- Camera failures

Console output includes `[DEBUG]` logs to aid in troubleshooting.

