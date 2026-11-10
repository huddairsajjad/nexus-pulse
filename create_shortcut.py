"""
Utility to create Windows Desktop Shortcut for H.Huddair's Nexus-Pulse.
"""
import os
import subprocess
from pathlib import Path


def create_desktop_shortcut():
    desktop = Path(os.environ.get("USERPROFILE", "C:/Users/STONE")) / "Desktop"
    target_bat = Path(__file__).resolve().parent / "Launch_Nexus_Pulse.bat"
    shortcut_path = desktop / "H.Huddair Nexus-Pulse.lnk"
    icon_source = Path(__file__).resolve().parent / "ui" / "assets" / "icon.ico"

    vbs_script = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target_bat}"
oLink.WorkingDirectory = "{target_bat.parent}"
oLink.Description = "H.Huddair's Nexus-Pulse Autonomous B2B Lead Engine"
oLink.WindowStyle = 1
oLink.Save
"""
    vbs_temp = target_bat.parent / "_create_shortcut.vbs"
    with open(vbs_temp, "w", encoding="utf-8") as f:
        f.write(vbs_script)

    try:
        subprocess.run(["cscript", "//Nologo", str(vbs_temp)], check=True)
        print(f"[SUCCESS] Desktop shortcut created: {shortcut_path}")
    finally:
        if vbs_temp.exists():
            vbs_temp.unlink()


if __name__ == "__main__":
    create_desktop_shortcut()
