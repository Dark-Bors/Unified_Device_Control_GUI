# # core/syscheck.py
# import os, time, threading, yaml, cv2
# from datetime import datetime

# APP_TAG = "<UDC app>"

# def _log(bus, msg): bus.publish("log:line", f"{APP_TAG} [SysCheck] {msg}")

# def _ensure_dirs():
#     os.makedirs("reports", exist_ok=True)
#     os.makedirs("captures", exist_ok=True)

# def _now():
#     return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# class SysCheckRunner:
#     """
#     Orchestrates a system check defined in config/syscheck.yaml
#     Steps supported:
#       - ping
#       - camera_check { cams: [cam_a, cam_b] }
#       - arduino_sequence { sequence: [ {send: "CMD", verify:{method:'user_confirm',prompt:'...'}} ... ] }
#       - adu_check { actions: [ {do:'LIGHT_ON', verify:{...}}, ... ] }
#     Emits to bus:
#       - 'log:line'
#       - 'syscheck:progress' (dict)
#       - 'syscheck:done'     (dict: {ok:bool, report_path:str})
#     """
#     def __init__(self, bus, serial_manager, adu_client, cameras_cfg, syscheck_yaml="config/syscheck.yaml"):
#         self.bus = bus
#         self.serial = serial_manager
#         self.adu = adu_client
#         self.cameras_cfg = cameras_cfg or {}
#         self.yaml_path = syscheck_yaml

#         self._thread = None
#         _ensure_dirs()

#     # ---------- public ----------
#     def run_async(self):
#         if self._thread and self._thread.is_alive():
#             _log(self.bus, "System Check already running.")
#             return
#         self._thread = threading.Thread(target=self._run, daemon=True)
#         self._thread.start()

#     # ---------- internals ----------
#     def _run(self):
#         started = time.time()
#         report_lines = []
#         def add(line):
#             report_lines.append(f"[{_now()}] {line}")
#             _log(self.bus, line)

#         try:
#             add("Starting System Check…")

#             with open(self.yaml_path, "r", encoding="utf-8") as f:
#                 cfg = yaml.safe_load(f) or {}
#             steps = cfg.get("steps", [])

#             ok = True
#             for idx, step in enumerate(steps, 1):
#                 stype = step.get("type")
#                 self.bus.publish("syscheck:progress", {"step": idx, "type": stype})
#                 add(f"Step {idx}/{len(steps)}: {stype}")

#                 if stype == "ping":
#                     ok &= self._step_ping(add)

#                 elif stype == "camera_check":
#                     cams = step.get("cams", [])
#                     ok &= self._step_camera_check(cams, add)

#                 elif stype == "arduino_sequence":
#                     seq = step.get("sequence", [])
#                     ok &= self._step_arduino_sequence(seq, add)

#                 elif stype == "adu_check":
#                     acts = step.get("actions", [])
#                     ok &= self._step_adu_check(acts, add)

#                 else:
#                     add(f"Skipped unknown step: {stype}")

#                 if not ok:
#                     add("Stopping early due to failure.")
#                     break

#             # write report
#             duration = int(time.time() - started)
#             add(f"System Check finished in {duration}s. Result: {'OK' if ok else 'FAIL'}")
#             report_path = os.path.join("reports", f"syscheck_{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt")
#             with open(report_path, "w", encoding="utf-8") as f:
#                 f.write("\n".join(report_lines) + "\n")

#             self.bus.publish("syscheck:done", {"ok": ok, "report_path": report_path})
#         except Exception as e:
#             add(f"System Check error: {e}")
#             self.bus.publish("syscheck:done", {"ok": False, "report_path": None})

#     # ---------- steps ----------
#     def _step_ping(self, add):
#         try:
#             if not (self.serial and self.serial.port):
#                 add("Serial not connected; running quick scan attempt.")
#             # Try a direct ping if serial is up
#             if self.serial and self.serial.port:
#                 self.serial.write_line("PING gui")
#                 time.sleep(0.3)
#                 add("PING sent on current port.")
#                 return True
#             add("No active port to ping.")
#             return False
#         except Exception as e:
#             add(f"Ping failed: {e}")
#             return False

#     def _step_camera_check(self, cams, add):
#         ok = True
#         for cam_key in cams:
#             c = self.cameras_cfg.get(cam_key, {})
#             idx = c.get("index", 0)
#             w, h = c.get("width", 640), c.get("height", 480)
#             add(f"Camera '{cam_key}' (index={idx}) — opening…")
#             cap = cv2.VideoCapture(int(idx))
#             if not cap or not cap.isOpened():
#                 add(f"Camera '{cam_key}' FAILED to open.")
#                 ok = False
#                 continue
#             cap.set(cv2.CAP_PROP_FRAME_WIDTH,  w)
#             cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
#             ret, frame = cap.read()
#             if not ret or frame is None:
#                 add(f"Camera '{cam_key}' FAILED to capture frame.")
#                 ok = False
#             else:
#                 snap_path = os.path.join("captures", f"syscheck_{cam_key}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.png")
#                 try:
#                     cv2.imwrite(snap_path, frame)
#                     add(f"Camera '{cam_key}' snapshot saved: {snap_path}")
#                 except Exception as e:
#                     add(f"Camera '{cam_key}' snapshot save error: {e}")
#             cap.release()
#         return ok

#     def _step_arduino_sequence(self, sequence, add):
#         if not self.serial or not self.serial.port:
#             add("Arduino not connected; cannot run sequence.")
#             return False
#         ok = True
#         for i, item in enumerate(sequence, 1):
#             cmd = item.get("send")
#             verify = item.get("verify", {})
#             add(f"Arduino seq {i}: send '{cmd}'")
#             if not self.serial.write_line(cmd):
#                 add(f"Write failed for '{cmd}'")
#                 ok = False
#                 break
#             time.sleep(0.4)

#             # optional user confirm
#             if verify and verify.get("method") == "user_confirm":
#                 prompt = verify.get("prompt", "Confirm?")
#                 res = self._yes_no_dialog(prompt)
#                 add(f"User confirm: {'YES' if res else 'NO'} — {prompt}")
#                 ok &= bool(res)
#                 if not ok:
#                     break
#         return ok

#     def _step_adu_check(self, actions, add):
#         if not self.adu or not self.adu.is_connected():
#             add("ADU not connected; attempting connect…")
#             if not self.adu.connect():
#                 add("ADU connect failed.")
#                 return False
#         ok = True
#         for i, act in enumerate(actions, 1):
#             name = act.get("do")
#             add(f"ADU action {i}: {name}")
#             if not self.adu.action(name):
#                 add(f"ADU action failed: {name}")
#                 ok = False
#                 break
#             verify = act.get("verify", {})
#             if verify and verify.get("method") == "user_confirm":
#                 prompt = verify.get("prompt", "Confirm?")
#                 res = self._yes_no_dialog(prompt)
#                 add(f"User confirm: {'YES' if res else 'NO'} — {prompt}")
#                 ok &= bool(res)
#                 if not ok:
#                     break
#         return ok

#     # ---------- tiny modal confirm ----------
#     def _yes_no_dialog(self, prompt: str) -> bool:
#         # Minimal, inline CTk dialog to avoid extra deps
#         import customtkinter as ctk

#         result = {"val": None}
#         win = ctk.CTkToplevel()
#         win.title("Confirm")
#         win.attributes("-topmost", True)
#         win.grab_set()
#         ctk.CTkLabel(win, text=prompt, wraplength=360, justify="left").pack(padx=16, pady=(16, 8))
#         row = ctk.CTkFrame(win); row.pack(pady=12)
#         def yes():
#             result["val"] = True
#             win.destroy()
#         def no():
#             result["val"] = False
#             win.destroy()
#         ctk.CTkButton(row, text="Yes", width=90, command=yes).pack(side="left", padx=8)
#         ctk.CTkButton(row, text="No",  width=90, command=no).pack(side="left", padx=8)
#         win.bind("<Return>", lambda _e: yes())
#         win.bind("<Escape>", lambda _e: no())
#         win.update()
#         # Center it roughly over parent
#         try:
#             parent = win.master.winfo_toplevel()
#             wx, wy = parent.winfo_rootx(), parent.winfo_rooty()
#             ww, wh = 420, 140
#             win.geometry(f"{ww}x{wh}+{wx+60}+{wy+60}")
#         except Exception:
#             pass
#         win.mainloop()
#         return bool(result["val"])
