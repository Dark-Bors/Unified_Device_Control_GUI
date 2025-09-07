# Entry point
import os, sys, logging, time
import customtkinter as ctk
import yaml
from version import __version__
from ui.main_window import MainWindow

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def setup_logging(cfg):
    folder = cfg["logging"]["folder"]
    os.makedirs(folder, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    logfile = os.path.join(folder, f"app_{ts}.log")

    level = getattr(logging, cfg["logging"].get("level", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    logging.info("==== App start ====")
    logging.info("Log file: %s", logfile)
    return logfile

def main():
    app_cfg = load_yaml(os.path.join("config", "app.yaml"))
    ctk.set_appearance_mode(app_cfg["app"]["theme"]["appearance"])
    ctk.set_default_color_theme(app_cfg["app"]["theme"]["color_theme"])
    logfile = setup_logging(app_cfg)

    root = MainWindow(app_cfg=app_cfg, logfile=logfile, version=__version__)
    root.mainloop()

if __name__ == "__main__":
    main()
