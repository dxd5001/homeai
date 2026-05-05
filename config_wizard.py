"""
Configuration Wizard for HomeAI Desktop App
===========================================
Step-by-step setup wizard for first-time configuration
"""

from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QTextEdit,
    QMessageBox,
    QCheckBox,
)

from config_manager import ConfigManager
from auto_start import AutoStartManager


class ConfigWizard(QWizard):
    """Configuration setup wizard"""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the wizard"""
        super().__init__()
        self.config = config_manager
        self.setWindowTitle("Home AI Setup")
        self.resize(600, 500)

        # Add pages
        self.addPage(LanguagePage(self.config))
        self.addPage(LLMChoicePage(self.config))
        self.addPage(LocalLLMPage(self.config))
        self.addPage(OpenAIPage(self.config))
        self.addPage(AutoStartPage(self.config))
        self.addPage(ConfirmationPage(self.config))

    def nextId(self):
        """Determine the next page ID based on current page and configuration"""
        current_id = self.currentId()

        # Skip OpenAIPage if Local LLM is selected
        if current_id == 1:  # LLMChoicePage
            if self.config.get("use_local_llm", True):
                # Skip OpenAIPage (ID 3) and go to AutoStartPage (ID 4)
                return 4
            else:
                # Go to OpenAIPage (ID 3)
                return 3

        # Default behavior: go to next page
        return super().nextId()

    def accept(self):
        """Save configuration when wizard is accepted"""
        # Save configuration from all pages
        self.config.save_config()
        self.config.mark_first_run_complete()
        super().accept()


class LanguagePage(QWizardPage):
    """Language selection page"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setTitle("Language")
        self.setSubTitle("Select your preferred language")

        layout = QVBoxLayout()

        language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItem("日本語", "ja")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("中文", "zh")
        self.language_combo.addItem("Español", "es")
        self.language_combo.addItem("Français", "fr")

        # Set default from config
        current_lang = self.config.get("language", "ja")
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break

        # Connect signal to enable/disable continue button
        self.language_combo.currentIndexChanged.connect(self.completeChanged)

        layout.addWidget(language_label)
        layout.addWidget(self.language_combo)
        layout.addStretch()
        self.setLayout(layout)

    def isComplete(self):
        """Check if page is complete"""
        return self.language_combo.currentData() is not None

    def initializePage(self):
        """Initialize page when shown"""
        # Set language from config
        current_lang = self.config.get("language", "ja")
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break

    def validatePage(self):
        """Validate page before proceeding"""
        language = self.language_combo.currentData()
        self.config.set("language", language)
        return True


class LLMChoicePage(QWizardPage):
    """LLM provider choice page"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setTitle("LLM Provider")
        self.setSubTitle("Choose your LLM provider")

        layout = QVBoxLayout()

        self.local_radio = QRadioButton("Local LLM (LM Studio, llama.cpp, etc.)")
        self.openai_radio = QRadioButton("OpenAI API")

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.local_radio, 1)
        self.button_group.addButton(self.openai_radio, 2)

        # Set default from config
        if self.config.get("use_local_llm", True):
            self.local_radio.setChecked(True)
        else:
            self.openai_radio.setChecked(True)

        # Connect signals to enable/disable continue button
        self.local_radio.toggled.connect(self.completeChanged)
        self.openai_radio.toggled.connect(self.completeChanged)

        layout.addWidget(self.local_radio)
        layout.addWidget(self.openai_radio)
        layout.addStretch()
        self.setLayout(layout)

    def isComplete(self):
        """Check if page is complete"""
        return self.local_radio.isChecked() or self.openai_radio.isChecked()

    def validatePage(self):
        """Validate page before proceeding"""
        use_local = self.local_radio.isChecked()
        self.config.set("use_local_llm", use_local)
        return True


class LocalLLMPage(QWizardPage):
    """Local LLM configuration page"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setTitle("Local LLM Settings")
        self.setSubTitle("Configure your local LLM")

        layout = QVBoxLayout()

        # Base URL
        url_label = QLabel("Base URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://127.0.0.1:1235/v1")
        self.url_input.setText(
            self.config.get("local_llm_base_url", "http://127.0.0.1:1235/v1")
        )

        # Model name
        model_label = QLabel("Model Name:")
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("google/gemma-4-e4b")
        self.model_input.setText(
            self.config.get("local_llm_model", "google/gemma-4-e4b")
        )

        # Help text
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(100)
        help_text.setText(
            "Make sure your local LLM (LM Studio, llama.cpp, etc.) is running in API server mode.\n"
            "Default LM Studio port is 1234, but you can change it in LM Studio settings."
        )

        # Connect signals to enable/disable continue button
        self.url_input.textChanged.connect(self.completeChanged)
        self.model_input.textChanged.connect(self.completeChanged)

        layout.addWidget(url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(model_label)
        layout.addWidget(self.model_input)
        layout.addWidget(help_text)
        layout.addStretch()
        self.setLayout(layout)

    def isComplete(self):
        """Check if page is complete"""
        return bool(self.url_input.text().strip() and self.model_input.text().strip())

    def validatePage(self):
        """Validate page before proceeding"""
        base_url = self.url_input.text().strip()
        model_name = self.model_input.text().strip()

        if not base_url or not model_name:
            QMessageBox.warning(self, "Validation Error", "Please fill in all fields.")
            return False

        self.config.set("local_llm_base_url", base_url)
        self.config.set("local_llm_model", model_name)
        return True


class OpenAIPage(QWizardPage):
    """OpenAI API configuration page"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setTitle("OpenAI API Settings")
        self.setSubTitle("Configure OpenAI API")

        layout = QVBoxLayout()

        # API Key
        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxxxxxx")
        self.api_key_input.setText(self.config.get("openai_api_key", ""))

        # Warning text
        warning_text = QTextEdit()
        warning_text.setReadOnly(True)
        warning_text.setMaximumHeight(150)
        warning_text.setStyleSheet("color: orange;")
        warning_text.setText(
            "⚠️ WARNING: OpenAI API uses pay-as-you-go pricing.\n"
            "You will be charged based on your API usage.\n"
            "Please check OpenAI pricing before using this option.\n\n"
            "We recommend using Local LLM for free and private usage."
        )

        # Connect signal to enable/disable continue button
        self.api_key_input.textChanged.connect(self.completeChanged)

        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(warning_text)
        layout.addStretch()
        self.setLayout(layout)

    def isComplete(self):
        """Check if page is complete"""
        return bool(self.api_key_input.text().strip())

    def validatePage(self):
        """Validate page before proceeding"""
        api_key = self.api_key_input.text().strip()

        if not api_key:
            QMessageBox.warning(
                self, "Validation Error", "Please enter your OpenAI API key."
            )
            return False

        self.config.set("openai_api_key", api_key)
        return True


class ConfirmationPage(QWizardPage):
    """Configuration confirmation page"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setTitle("Confirmation")
        self.setSubTitle("Review your configuration")

        layout = QVBoxLayout()

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)

        layout.addWidget(self.summary_text)
        self.setLayout(layout)

    def initializePage(self):
        """Initialize page when shown"""
        language = self.config.get("language", "ja")
        use_local = self.config.get("use_local_llm", True)
        auto_start = self.config.get("auto_start", False)

        summary = f"Language: {language}\n\n"

        if use_local:
            summary += "LLM Provider: Local LLM\n"
            summary += f"Base URL: {self.config.get('local_llm_base_url')}\n"
            summary += f"Model: {self.config.get('local_llm_model')}\n"
        else:
            summary += "LLM Provider: OpenAI API\n"
            summary += f"API Key: {'*' * 20}\n"  # Mask API key

        summary += f"\nAuto-start: {'Enabled' if auto_start else 'Disabled'}\n"

        self.summary_text.setText(summary)


class AutoStartPage(QWizardPage):
    """Auto-start configuration page"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.auto_start_manager = AutoStartManager()
        self.setTitle("Auto-start")
        self.setSubTitle("Configure auto-start on system boot")

        layout = QVBoxLayout()

        self.auto_start_checkbox = QCheckBox("Enable auto-start on system boot")
        self.auto_start_checkbox.setChecked(self.config.get("auto_start", False))

        # Help text
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(100)
        help_text.setText(
            "If enabled, Home AI will automatically start when you log in to your computer.\n"
            "You can always change this setting later from the Settings menu."
        )

        layout.addWidget(self.auto_start_checkbox)
        layout.addWidget(help_text)
        layout.addStretch()
        self.setLayout(layout)

    def isComplete(self):
        """Check if page is complete"""
        return True  # Auto-start is always valid (checkbox can be checked or unchecked)

    def validatePage(self):
        """Validate page before proceeding"""
        auto_start = self.auto_start_checkbox.isChecked()
        self.config.set("auto_start", auto_start)

        # Enable/disable auto-start (do this after wizard completes)
        # Don't do it here to avoid blocking the wizard
        # This will be handled by the desktop app after wizard completes

        return True
