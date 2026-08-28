"""
Cross-platform autostart management for GDriveCloner.
"""
import os
import sys

def is_windows():
    return sys.platform == 'win32'

def is_macos():
    return sys.platform == 'darwin'

APP_NAME = "GDriveCloner"

def _get_executable_path():
    """Return the path to the current executable or script."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        # Running as a python script
        script = os.path.abspath(sys.argv[0])
        return f'{sys.executable} "{script}"'

# --- Windows ---
def _win_get_reg_key():
    import winreg
    return winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_ALL_ACCESS,
    )

def _win_enable_autostart():
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        exe_path = _get_executable_path()
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error enabling Windows autostart: {e}")
        return False

def _win_disable_autostart():
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return True
    except Exception as e:
        print(f"Error disabling Windows autostart: {e}")
        return False

def _win_is_autostart_enabled():
    import winreg
    try:
        key = _win_get_reg_key()
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False

# --- macOS ---
def _mac_get_plist_path():
    return os.path.expanduser(f"~/Library/LaunchAgents/com.{APP_NAME.lower()}.plist")

def _mac_enable_autostart():
    plist_path = _mac_get_plist_path()
    exe_path = getattr(sys, 'frozen', False) and sys.executable or os.path.abspath(sys.argv[0])
    
    # If running as script, we need both python and the script path in ProgramArguments
    if getattr(sys, 'frozen', False):
        args_xml = f"<string>{exe_path}</string>"
    else:
        args_xml = f"<string>{sys.executable}</string>\n        <string>{exe_path}</string>"

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{APP_NAME.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        {args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
    try:
        os.makedirs(os.path.dirname(plist_path), exist_ok=True)
        with open(plist_path, "w") as f:
            f.write(plist_content)
        return True
    except Exception as e:
        print(f"Error enabling macOS autostart: {e}")
        return False

def _mac_disable_autostart():
    plist_path = _mac_get_plist_path()
    try:
        if os.path.exists(plist_path):
            os.remove(plist_path)
        return True
    except Exception as e:
        print(f"Error disabling macOS autostart: {e}")
        return False

def _mac_is_autostart_enabled():
    return os.path.exists(_mac_get_plist_path())

# --- Public API ---

def enable():
    if is_windows(): return _win_enable_autostart()
    if is_macos(): return _mac_enable_autostart()
    return False

def disable():
    if is_windows(): return _win_disable_autostart()
    if is_macos(): return _mac_disable_autostart()
    return False

def is_enabled():
    if is_windows(): return _win_is_autostart_enabled()
    if is_macos(): return _mac_is_autostart_enabled()
    return False

def set_state(enabled: bool):
    if enabled:
        return enable()
    else:
        return disable()
