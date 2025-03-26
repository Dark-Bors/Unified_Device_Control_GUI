# servo_GUI

import customtkinter as ctk
import threading
import time
import serial.tools.list_ports


class ServoFrame(ctk.CTkFrame):
    def __init__(self, master, serial_connection=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Serial connection passed from main GUI
        self.serial_connection = serial_connection

        # Timer state variables
        self.timer_active = False
        self.on_time = 10             # Seconds the servo stays ON
        self.off_time = 5             # Seconds the servo stays OFF
        self.max_cycles = 20          # Maximum number of ON/OFF cycles

        # === UI Elements ===

        # Title Label
        ctk.CTkLabel(self, text="Servo Control").pack(pady=5)

        # Manual control buttons
        ctk.CTkButton(self, text="Move Clockwise", command=self.clockwise_short).pack(pady=5)
        ctk.CTkButton(self, text="Move Counterclockwise", command=self.counterclockwise_short).pack(pady=5)

        # Timer control buttons
        ctk.CTkButton(self, text="Start Timer", command=self.start_clockwise_timer).pack(pady=5)
        ctk.CTkButton(self, text="Stop Timer", command=self.stop_timer).pack(pady=5)

        # Connection status label
        self.status_label = ctk.CTkLabel(self, text="Status: Disconnected")
        self.status_label.pack(pady=5)

        # Timer activity label (live updates)
        self.timer_label = ctk.CTkLabel(self, text="Timer: Not Running")
        self.timer_label.pack(pady=5)

        # Update status label based on connection
        if self.serial_connection and self.serial_connection.is_open:
            self.status_label.configure(text="Status: Connected (shared)")
        else:
            self.status_label.configure(text="Status: Disconnected")

    def send_command(self, cmd):
        """Send a command to the device via serial."""
        print(f"[DEBUG] send_command was called with: {cmd}")
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write(f"{cmd}\n".encode())
            print(f"Sent: {cmd}")
        else:
            print("[DEBUG] Serial connection not open")

    def clockwise_short(self):
        """Move servo clockwise for 2 seconds."""
        print("[DEBUG] clockwise_short called")
        self.send_command("CLOCKWISE")
        time.sleep(2)
        self.send_command("STOP")

    def counterclockwise_short(self):
        """Move servo counterclockwise for a short pulse."""
        print("[DEBUG] counterclockwise_short called")
        self.send_command("COUNTERCLOCKWISE")
        time.sleep(0.03)
        self.send_command("STOP")

    def start_clockwise_timer(self):
        """Start servo ON/OFF timer cycle loop in a separate thread."""
        print("[DEBUG] start_clockwise_timer called")
        if self.timer_active:
            print("[DEBUG] Timer already active. Skipping.")
            return

        self.timer_active = True

        def loop():
            print("[DEBUG] Timer thread started")
            for cycle in range(1, self.max_cycles + 1):
                if not self.timer_active:
                    print("[DEBUG] Timer stopped early")
                    break

                # === ON Phase ===
                self.send_command("CLOCKWISE")
                for remaining in range(self.on_time, 0, -1):
                    if not self.timer_active:
                        break
                    self.timer_label.configure(text=f"Cycle {cycle}: ON ({remaining}s remaining)")
                    time.sleep(1)
                self.send_command("STOP")

                if not self.timer_active:
                    print("[DEBUG] Timer stopped early after ON")
                    break

                # === OFF Phase ===
                for remaining in range(self.off_time, 0, -1):
                    if not self.timer_active:
                        break
                    self.timer_label.configure(text=f"Cycle {cycle}: OFF ({remaining}s) remaining")
                    time.sleep(1)

            # === After timer ends ===
            self.timer_active = False
            self.timer_label.configure(text="Timer: Finished or Stopped")
            self.status_label.configure(text="Status: Timer stopped")
            print("[DEBUG] Timer loop ended")

        # Start the loop in a separate thread so GUI stays responsive
        threading.Thread(target=loop, daemon=True).start()

    def stop_timer(self):
        """Stop the timer loop and send a STOP command to the servo."""
        print("[DEBUG] stop_timer called")
        self.timer_active = False
        self.send_command("STOP")
