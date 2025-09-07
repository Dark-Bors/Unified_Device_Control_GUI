# Unified Device Control GUI 2

**Version:** 0.4.0-alpha

**Author:** Dark Bors =]

**License:** MIT

**Platform:** Windows (due to ADU DLL dependency)

A Python-based GUI for controlling and automating multiple lab devices from a single interface.
Supports Arduino-based modules, ADU USB relays, dual USB cameras, and stepper/capsule/link controls — with real-time logging, YAML-driven configuration, and robust error handling.

---

## 🚀 Features

* 🎛️ Unified control panel for Arduino, ADU, and cameras
* 🔁 Ping–Pong serial discovery with connect/disconnect
* 📷 **Dual camera support** (CamA + CamB) with toggles, snapshots, recording
* ⚙️ Arduino commands (Capsule, Link Device, Stepper, Version, Reset, Help)
* 🔌 ADU USB relay control (USB ON/OFF, Light ON/OFF)
* ✅ Status bar with uptime and connection state
* 🪵 Built-in **serial monitor** with timestamps, search, save/clear
* 🧪 **System Check** (manual mode now, assisted/auto planned)
* 🗂 YAML-based config for commands, serial settings, cameras, and test steps
* 📑 Auto-generated logs in `/logs/` with timestamped filenames

---

## 🧭 GUI Layout Overview

> *(screenshots to be added in `/assets/img/`)*

* **Status Bar** (top): Ready/Connected/Scanning with uptime
* **Dual Cameras** (CamA, CamB): each toggleable ON/OFF, snapshot, record
* **Serial Monitor** (bottom wide): live log, filters, save/clear
* **Right Panel (Actions):**

  * Arduino Control (Capsule/Link/Motor/etc.)
  * ADU Control (USB/Light)
  * Buttons: Scan, Connect, Disconnect, System Check, Exit

---

## 🧱 Project Structure

```
app.py
│
├── config/
│   ├── app.yaml          # App/theme/logging/serial/camera settings
│   ├── commands.yaml     # Arduino + ADU button mappings
│   └── syscheck.yaml     # System Check steps and rules
│
├── core/
│   ├── serial_manager.py # Serial open/read/write
│   ├── device_scanner.py # Ping–Pong COM scan
│   ├── camera_worker.py  # OpenCV capture worker
│   ├── adu_client.py     # ADU DLL interface (stub now)
│   ├── event_bus.py      # Thread-safe pub/sub
│   ├── syscheck.py       # System check orchestrator
│   └── vision_check.py   # Motion/brightness verification (future)
│
├── ui/
│   ├── main_window.py
│   └── panels/
│       ├── status_bar.py
│       ├── camera_panel.py
│       ├── arduino_panel.py
│       ├── adu_panel.py
│       └── log_panel.py
│
├── logs/                 # Auto-created session logs
├── captures/             # Snapshots & recordings
├── reports/              # System check reports
├── version.py
├── requirements.txt
└── README.md
```

---

## 🛠️ Installation

### Clone the repository

```bash
git clone https://github.com/Dark-Bors/Unified_Device_Control_GUI.git
cd Unified_Device_Control_GUI
```

### Create a virtual environment (recommended)

```bash
python -m venv .venv
.venv\Scripts\activate   # On Windows
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

```bash
python app.py
```

---

## 📦 Requirements

* Windows OS (for ADU DLL support)
* Python 3.10+
* Arduino board with loaded firmware (provides PING/PONG + commands)
* (Optional) Ontrak ADU USB Relay (e.g., ADU200 series)
* (Optional) Dual USB Cameras

### Python Libraries

```
customtkinter>=5.2.0
opencv-python
Pillow
pyserial
pyyaml
```

---

## 🔌 Arduino Commands (currently supported)

* `C_ON` / `C_OFF` → Capsule ON/OFF
* `LD_ON` / `LD_OFF` → Link Device ON/OFF
* `M_ON` → Stepper start cycle (MOV=5.4s, STOP=5s)
* `M_ON_C` → Stepper start constant (delay=20 ms)
* `M_OFF` → Stop stepper motor
* `VER` → Print firmware version
* `RESET` → Reset Arduino + stop motor
* `HELP` → Show available commands

---

## 🔌 ADU USB Relay

* `USB_ON` / `USB_OFF`
* `LIGHT_ON` / `LIGHT_OFF`

*(requires AduHid64.dll in `utils/adu_python_dll/ontrak/`)*

---

## 🧪 System Check (planned)

1. Ping–Pong port check
2. Camera availability check
3. Arduino motion/servo sequence (manual confirm or vision detect)
4. ADU toggling (manual confirm or brightness detect)
5. Report saved in `/reports/`

---

## 🧯 Error Handling

* Device not connected
* Serial/COM issues
* DLL loading failures
* Camera open failures

Logs are always written to `logs/app_YYYYMMDD-HHMMSS.log` in addition to the GUI monitor.

---

Would you like me to drop this in **as a new `README.md` file** ready to commit in your `v0.4.0_dev` branch?
