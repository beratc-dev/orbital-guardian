from __future__ import annotations

import subprocess
import sys

COMMAND = [
    sys.executable,
    "main.py",
    "--targets",
    "TURKSAT 5A",
    "TURKSAT 5B",
    "GOKTURK-1",
    "--hours",
    "72",
    "--step-minutes",
    "10",
    "--top-k",
    "15",
]

if __name__ == "__main__":
    raise SystemExit(subprocess.call(COMMAND))
