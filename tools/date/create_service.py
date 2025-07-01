import os
import sys

# Force Python not to create .pyc files
sys.dont_write_bytecode = True

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICE_TEMPLATE = """
[Unit]
Description=Synchronize system date and time.
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {script_path}/script.py
""".strip()


TIMER_TEMPLATE = """
[Unit]
Description=Timer for running {name_service}

[Timer]
OnBootSec=60sec
OnUnitActiveSec=1h
Unit={name_service}

[Install]
WantedBy=timers.target
""".strip()

def create():
    service_content = SERVICE_TEMPLATE.format(script_path=SCRIPT_DIR)
    return service_content, SCRIPT_DIR

def create_timer(name_service: str):
    _content = TIMER_TEMPLATE.format(name_service=name_service)
    return _content, SCRIPT_DIR