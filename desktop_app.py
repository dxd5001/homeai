"""
HomeAI Desktop Application
==========================
PyQt6-based desktop app with system tray integration
"""

import sys

from PyQt6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QMessageBox,
)
from PyQt6.QtGui import QAction

from config_manager import ConfigManager
from config_wizard import ConfigWizard


class HomeAIApp:
    """Main HomeAI Desktop Application"""

    def __init__(self):
        """Initialize the application"""
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when window closed

        # Load configuration
        self.config = ConfigManager()

        # Setup system tray
        self.tray_icon = None
        self.setup_tray_icon()

        # Check if first run
        if self.config.is_first_run():
            self.show_first_run_wizard()

    def setup_tray_icon(self):
        """Setup system tray icon"""
        # Create tray icon (will use default icon for now)
        self.tray_icon = QSystemTrayIcon()

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

    def show_first_run_wizard(self):
        """Show first-run setup wizard"""
        wizard = ConfigWizard(self.config)
        if wizard.exec():
            # Wizard completed successfully
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
        # TODO: Launch Streamlit in WebView
        QMessageBox.information(
            None, "Home AI", "Web UI will be opened here (TODO: implement WebView)"
        )

    def open_settings(self):
        """Open settings dialog"""
        # TODO: Launch settings dialog
        QMessageBox.information(
            None, "Home AI", "Settings dialog will be opened here (TODO: implement)"
        )

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
