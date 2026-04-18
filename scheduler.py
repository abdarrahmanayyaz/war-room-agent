"""macOS launchd auto-scout scheduler — install/uninstall 7am daily scout."""

import os
import subprocess
import sys
from pathlib import Path

PLIST_NAME = "com.warroom.scout"
PLIST_FILENAME = f"{PLIST_NAME}.plist"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
PROJECT_DIR = Path(__file__).parent.resolve()
SCOUT_PATH = PROJECT_DIR / "scout.py"
VENV_PYTHON = PROJECT_DIR / "venv" / "bin" / "python3"

PLIST_CONTENT = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{VENV_PYTHON}</string>
        <string>{SCOUT_PATH}</string>
        <string>--auto</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>{PROJECT_DIR}</string>
    <key>StandardOutPath</key>
    <string>{PROJECT_DIR / "data" / "scout_stdout.log"}</string>
    <key>StandardErrorPath</key>
    <string>{PROJECT_DIR / "data" / "scout_stderr.log"}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
"""


def install():
    """Install the launchd plist for daily auto-scout at 7am."""
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    plist_path = LAUNCH_AGENTS_DIR / PLIST_FILENAME

    # Write plist
    with open(plist_path, "w") as f:
        f.write(PLIST_CONTENT)
    print(f"Wrote plist to {plist_path}")

    # Unload if already loaded
    subprocess.run(
        ["launchctl", "unload", str(plist_path)],
        capture_output=True,
    )

    # Load
    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("Auto-scout installed. Will run daily at 7:00 AM.")
        print(f"Logs: {PROJECT_DIR / 'data' / 'scout_stdout.log'}")
    else:
        print(f"Error loading plist: {result.stderr}")


def uninstall():
    """Uninstall the launchd plist."""
    plist_path = LAUNCH_AGENTS_DIR / PLIST_FILENAME
    if plist_path.exists():
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
        )
        plist_path.unlink()
        print("Auto-scout uninstalled.")
    else:
        print("Auto-scout not installed.")


def status() -> bool:
    """Check if auto-scout is installed and loaded."""
    result = subprocess.run(
        ["launchctl", "list", PLIST_NAME],
        capture_output=True, text=True,
    )
    return result.returncode == 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scheduler.py [install|uninstall|status]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "install":
        install()
    elif cmd == "uninstall":
        uninstall()
    elif cmd == "status":
        is_loaded = status()
        print(f"Auto-scout: {'ACTIVE' if is_loaded else 'NOT INSTALLED'}")
    else:
        print(f"Unknown command: {cmd}")
