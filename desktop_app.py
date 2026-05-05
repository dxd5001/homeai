"""
HomeAI Desktop Application
==========================
PyQt6-based desktop app with system tray integration
"""

import sys
from pathlib import Path

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtCore import QThread, pyqtSignal

from config_manager import ConfigManager
from config_wizard import ConfigWizard
from auto_start import AutoStartManager
from prompts import PromptTemplates


class ChatWorker(QThread):
    """Worker thread for generating AI responses"""

    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, chain_with_history, message: str, session_id: str):
        super().__init__()
        self.chain_with_history = chain_with_history
        self.message = message
        self.session_id = session_id

    def run(self):
        """Generate response in background thread"""
        try:
            response = self.chain_with_history.invoke(
                {"input": self.message},
                config={"configurable": {"session_id": self.session_id}},
            )
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ChatWindow(QMainWindow):
    """Native chat window for Home AI"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.store: dict[str, InMemoryChatMessageHistory] = {}
        self.session_id = "default-session"
        self.worker = None

        self.setWindowTitle("Home AI")
        self.resize(1200, 800)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("メッセージを入力...")
        self.input_field.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        provider_label = QLabel(self.get_model_info())

        layout = QVBoxLayout()
        layout.addWidget(provider_label)
        layout.addWidget(self.chat_history)
        layout.addLayout(input_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.chain_with_history = self.create_chain_with_history()

    def get_model_info(self):
        """Get current model information"""
        if self.config.get("use_local_llm", True):
            base_url = self.config.get("local_llm_base_url", "http://127.0.0.1:1235/v1")
            model = self.config.get("local_llm_model", "google/gemma-4-e4b")
            return f"Local LLM: {model} ({base_url})"
        return "OpenAI API: gpt-4o-mini"

    def create_model(self):
        """Create chat model from configuration"""
        if self.config.get("use_local_llm", True):
            return ChatOpenAI(
                base_url=self.config.get(
                    "local_llm_base_url", "http://127.0.0.1:1235/v1"
                ),
                api_key="dummy",
                model=self.config.get("local_llm_model", "google/gemma-4-e4b"),
                temperature=0.7,
            )

        openai_api_key = self.config.get("openai_api_key", "")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        return ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o-mini",
            temperature=0.7,
        )

    def create_chain_with_history(self):
        """Create LangChain chain with conversation history"""
        language = self.config.get("language", "ja")
        prompt = PromptTemplates.create_prompt_template(language)
        chain = prompt | self.create_model() | StrOutputParser()
        return RunnableWithMessageHistory(
            chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )

    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        """Return history object linked to session ID"""
        if session_id not in self.store:
            self.store[session_id] = InMemoryChatMessageHistory()
        return self.store[session_id]

    def send_message(self):
        """Send user message to AI"""
        message = self.input_field.text().strip()
        if not message or self.worker is not None:
            return

        self.append_message("You", message)
        self.input_field.clear()
        self.set_input_enabled(False)
        self.append_message("AI", "考え中...")

        self.worker = ChatWorker(self.chain_with_history, message, self.session_id)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(self.cleanup_worker)
        self.worker.start()

    def append_message(self, sender: str, message: str):
        """Append message to chat history"""
        self.chat_history.append(f"<b>{sender}:</b> {message}")

    def handle_response(self, response: str):
        """Handle AI response"""
        self.append_message("AI", response)
        self.set_input_enabled(True)

    def handle_error(self, error_message: str):
        """Handle AI response error"""
        self.append_message("Error", error_message)
        self.set_input_enabled(True)

    def cleanup_worker(self):
        """Clean up finished worker"""
        self.worker = None

    def set_input_enabled(self, enabled: bool):
        """Enable or disable chat input"""
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)


class HomeAIApp:
    """Main HomeAI Desktop Application"""

    def __init__(self):
        """Initialize the application"""
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when window closed

        # Load configuration
        self.config = ConfigManager()

        # Chat window
        self.chat_window = None
        self.shortcut_widget = QWidget()

        # Setup system tray
        self.tray_icon = None
        self.setup_tray_icon()

        # Check if first run
        if self.config.is_first_run():
            self.show_first_run_wizard()

        # Setup global shortcut
        self.setup_global_shortcut()

        # Show notification about LM Studio if using Local LLM
        if self.config.get("use_local_llm", True):
            self.tray_icon.showMessage(
                "Home AI",
                "Make sure LM Studio is running in API server mode before using the chat.",
                QSystemTrayIcon.MessageIcon.Information,
                5000,
            )

    def setup_tray_icon(self):
        """Setup system tray icon"""
        # Create tray icon with standard icon
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon = QSystemTrayIcon(icon)

        # Create context menu
        menu = QMenu()

        # Open action
        open_action = QAction("Open Home AI", self.app)
        open_action.triggered.connect(self.open_chat_window)
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
        """Setup global shortcut to open chat window"""
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
        self.shortcut = QShortcut(shortcut_key, self.shortcut_widget)
        self.shortcut.activated.connect(self.open_chat_window)

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

    def open_chat_window(self):
        """Open the native chat window"""
        if self.chat_window is None or not self.chat_window.isVisible():
            try:
                self.chat_window = ChatWindow(self.config)
                self.chat_window.show()
            except Exception as e:
                QMessageBox.warning(
                    None,
                    "Home AI Error",
                    f"Failed to open Home AI chat window:\n{str(e)}",
                )
        else:
            self.chat_window.raise_()
            self.chat_window.activateWindow()

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
