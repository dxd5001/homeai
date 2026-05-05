"""
HomeAI Desktop Application
==========================
PyQt6-based desktop app with system tray integration
"""

import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QMessageBox,
    QMainWindow,
    QStyle,
)
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer

from config_manager import ConfigManager
from config_wizard import ConfigWizard
from auto_start import AutoStartManager


class WebViewWindow(QMainWindow):
    """WebView window for Streamlit UI"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.streamlit_process = None
        self.setWindowTitle("Home AI")
        self.resize(1200, 800)

        # Setup WebView
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)

        # Start Streamlit
        self.start_streamlit()

    def start_streamlit(self):
        """Start Streamlit process"""
        try:
            # Get script directory
            script_dir = Path(__file__).parent
            web_chatbot_path = script_dir / "web_chatbot.py"

            # Set environment variables from config
            env = os.environ.copy()
            env["USE_LOCAL_LLM"] = str(self.config.get("use_local_llm", True)).lower()
            env["LOCAL_LLM_BASE_URL"] = self.config.get(
                "local_llm_base_url", "http://127.0.0.1:1235/v1"
            )
            env["LOCAL_LLM_MODEL"] = self.config.get(
                "local_llm_model", "google/gemma-4-e4b"
            )
            env["LANGUAGE"] = self.config.get("language", "ja")

            if not self.config.get("use_local_llm", True):
                env["OPENAI_API_KEY"] = self.config.get("openai_api_key", "")

            # Start Streamlit process
            self.streamlit_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(web_chatbot_path),
                    "--server.headless",
                    "true",
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait a bit for Streamlit to start
            QTimer.singleShot(3000, self.load_streamlit_url)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start Streamlit: {str(e)}")

    def load_streamlit_url(self):
        """Load Streamlit URL in WebView"""
        self.web_view.setUrl(QUrl("http://localhost:8501"))

    def closeEvent(self, event):
        """Handle window close event"""
        if self.streamlit_process:
            self.streamlit_process.terminate()
            self.streamlit_process.wait()
        event.accept()


class HomeAIApp:
    """Main HomeAI Desktop Application"""

    def __init__(self):
        """Initialize the application"""
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when window closed

        # Load configuration
        self.config = ConfigManager()

        # WebView window
        self.web_view_window = None

        # Setup system tray
        self.tray_icon = None
        self.setup_tray_icon()

        # Check if first run
        if self.config.is_first_run():
            self.show_first_run_wizard()

        # Setup global shortcut
        self.setup_global_shortcut()

    def setup_tray_icon(self):
        """Setup system tray icon"""
        # Create tray icon with standard icon
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon = QSystemTrayIcon(icon)

        # Create context menu
        menu = QMenu()

        # Open action
        open_action = QAction("Open Home AI", self.app)
        open_action.triggered.connect(self.open_web_ui)
        menu.addAction(open_action)

        menu.addSeparator()

        # Settings action
        settings_action = QAction("Settings", self.app)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

        # Show tray icon
        self.tray_icon.show()

        # Show notification
        self.tray_icon.showMessage(
            "Home AI",
            "Home AI is running in the background",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def setup_global_shortcut(self):
        """Setup global shortcut to open web UI"""
        # Detect platform
        import platform

        is_macos = platform.system() == "Darwin"

        # Set shortcut key sequence
        if is_macos:
            # macOS: Cmd+Shift+H
            shortcut_key = QKeySequence("Ctrl+Shift+H")
        else:
            # Windows/Linux: Ctrl+Shift+H
            shortcut_key = QKeySequence("Ctrl+Shift+H")

        # Create shortcut
        shortcut = QShortcut(shortcut_key, self.app)
        shortcut.activated.connect(self.open_web_ui)

    def show_first_run_wizard(self):
        """Show first-run setup wizard"""
        wizard = ConfigWizard(self.config)
        if wizard.exec():
            # Wizard completed successfully
            # Apply auto-start setting
            auto_start_manager = AutoStartManager()
            if self.config.get("auto_start", False):
                script_path = str(Path(__file__))
                auto_start_manager.enable_auto_start(script_path)
            else:
                auto_start_manager.disable_auto_start()

            QMessageBox.information(
                None, "Setup Complete", "Home AI has been configured successfully!"
            )
        else:
            # Wizard was cancelled
            QMessageBox.warning(
                None,
                "Setup Cancelled",
                "You can configure Home AI later from the Settings menu.",
            )

    def open_web_ui(self):
        """Open the Streamlit web UI"""
        if self.web_view_window is None or not self.web_view_window.isVisible():
            self.web_view_window = WebViewWindow(self.config)
            self.web_view_window.show()
        else:
            self.web_view_window.raise_()
            self.web_view_window.activateWindow()

    def open_settings(self):
        """Open settings dialog"""
        wizard = ConfigWizard(self.config)
        wizard.exec()

    def quit_app(self):
        """Quit the application"""
        self.tray_icon.hide()
        self.app.quit()

    def run(self):
        """Run the application"""
        sys.exit(self.app.exec())


def main():
    """Main entry point"""
    app = HomeAIApp()
    app.run()


if __name__ == "__main__":
    main()
