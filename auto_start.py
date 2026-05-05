"""
Auto-start Manager for HomeAI Desktop App
=========================================
Handles OS-specific auto-start configuration
"""

import platform
import subprocess
import sys
from pathlib import Path


class AutoStartManager:
    """Manages auto-start configuration for different OS"""

    def __init__(self):
        """Initialize auto-start manager"""
        self.system = platform.system()
        self.app_name = "Home AI"

    def enable_auto_start(self, script_path: str) -> bool:
        """Enable auto-start for the application"""
        try:
            if self.system == "Darwin":
                return self._enable_macos_auto_start(script_path)
            elif self.system == "Windows":
                return self._enable_windows_auto_start(script_path)
            elif self.system == "Linux":
                return self._enable_linux_auto_start(script_path)
            else:
                print(f"Auto-start not supported on {self.system}")
                return False
        except Exception as e:
            print(f"Failed to enable auto-start: {e}")
            return False

    def disable_auto_start(self) -> bool:
        """Disable auto-start for the application"""
        try:
            if self.system == "Darwin":
                return self._disable_macos_auto_start()
            elif self.system == "Windows":
                return self._disable_windows_auto_start()
            elif self.system == "Linux":
                return self._disable_linux_auto_start()
            else:
                print(f"Auto-start not supported on {self.system}")
                return False
        except Exception as e:
            print(f"Failed to disable auto-start: {e}")
            return False

    def is_auto_start_enabled(self) -> bool:
        """Check if auto-start is enabled"""
        try:
            if self.system == "Darwin":
                return self._is_macos_auto_start_enabled()
            elif self.system == "Windows":
                return self._is_windows_auto_start_enabled()
            elif self.system == "Linux":
                return self._is_linux_auto_start_enabled()
            else:
                return False
        except Exception:
            return False

    def _enable_macos_auto_start(self, script_path: str) -> bool:
        """Enable auto-start on macOS using launchd"""
        # Create launchd plist file
        plist_path = (
            Path.home()
            / "Library"
            / "LaunchAgents"
            / f"com.homeai.{self.app_name.lower().replace(' ', '-')}.plist"
        )

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.homeai.{self.app_name.lower().replace(" ", "-")}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""

        plist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plist_path, "w") as f:
            f.write(plist_content)

        # Load the launch agent
        subprocess.run(["launchctl", "load", str(plist_path)], check=True)
        return True

    def _disable_macos_auto_start(self) -> bool:
        """Disable auto-start on macOS"""
        plist_path = (
            Path.home()
            / "Library"
            / "LaunchAgents"
            / f"com.homeai.{self.app_name.lower().replace(' ', '-')}.plist"
        )

        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], check=True)
            plist_path.unlink()
            return True
        return False

    def _is_macos_auto_start_enabled(self) -> bool:
        """Check if auto-start is enabled on macOS"""
        plist_path = (
            Path.home()
            / "Library"
            / "LaunchAgents"
            / f"com.homeai.{self.app_name.lower().replace(' ', '-')}.plist"
        )
        return plist_path.exists()

    def _enable_windows_auto_start(self, script_path: str) -> bool:
        """Enable auto-start on Windows using registry"""
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(
                key,
                self.app_name,
                0,
                winreg.REG_SZ,
                f'"{sys.executable}" "{script_path}"',
            )
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed to enable Windows auto-start: {e}")
            return False

    def _disable_windows_auto_start(self) -> bool:
        """Disable auto-start on Windows"""
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            # Key doesn't exist, already disabled
            return True
        except Exception as e:
            print(f"Failed to disable Windows auto-start: {e}")
            return False

    def _is_windows_auto_start_enabled(self) -> bool:
        """Check if auto-start is enabled on Windows"""
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, self.app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def _enable_linux_auto_start(self, script_path: str) -> bool:
        """Enable auto-start on Linux using systemd user service"""
        service_name = f"homeai-{self.app_name.lower().replace(' ', '-')}.service"
        service_path = Path.home() / ".config" / "systemd" / "user" / service_name

        service_content = f"""[Unit]
Description={self.app_name}
After=network.target

[Service]
Type=simple
ExecStart={sys.executable} {script_path}
Restart=on-failure

[Install]
WantedBy=default.target
"""

        service_path.parent.mkdir(parents=True, exist_ok=True)
        with open(service_path, "w") as f:
            f.write(service_content)

        # Enable and start the service
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", service_name], check=True)
        subprocess.run(["systemctl", "--user", "start", service_name], check=True)
        return True

    def _disable_linux_auto_start(self) -> bool:
        """Disable auto-start on Linux"""
        service_name = f"homeai-{self.app_name.lower().replace(' ', '-')}.service"
        service_path = Path.home() / ".config" / "systemd" / "user" / service_name

        try:
            subprocess.run(["systemctl", "--user", "stop", service_name], check=True)
            subprocess.run(["systemctl", "--user", "disable", service_name], check=True)
            if service_path.exists():
                service_path.unlink()
            return True
        except Exception as e:
            print(f"Failed to disable Linux auto-start: {e}")
            return False

    def _is_linux_auto_start_enabled(self) -> bool:
        """Check if auto-start is enabled on Linux"""
        service_name = f"homeai-{self.app_name.lower().replace(' ', '-')}.service"
        service_path = Path.home() / ".config" / "systemd" / "user" / service_name
        return service_path.exists()
