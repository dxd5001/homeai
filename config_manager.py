"""
Configuration Manager for HomeAI Desktop App
=============================================
Handles reading and writing configuration settings to config.json
"""

import json
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """Manages application configuration"""

    DEFAULT_CONFIG = {
        "language": "ja",
        "use_local_llm": True,
        "local_llm_base_url": "http://127.0.0.1:1235/v1",
        "local_llm_model": "google/gemma-4-e4b",
        "openai_api_key": "",
        "auto_start": False,
        "first_run": True,
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager with config file path"""
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to config.json in user's home directory
            self.config_path = Path.home() / ".homeai" / "config.json"

        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            return self.DEFAULT_CONFIG.copy()

    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value) -> bool:
        """Set configuration value and save"""
        self.config[key] = value
        return self.save_config()

    def get_all(self) -> Dict:
        """Get all configuration"""
        return self.config.copy()

    def update(self, config_dict: Dict) -> bool:
        """Update multiple configuration values"""
        self.config.update(config_dict)
        return self.save_config()

    def reset_to_default(self) -> bool:
        """Reset configuration to default values"""
        self.config = self.DEFAULT_CONFIG.copy()
        return self.save_config()

    def is_first_run(self) -> bool:
        """Check if this is the first run"""
        return self.config.get("first_run", True)

    def mark_first_run_complete(self) -> bool:
        """Mark first run as complete"""
        return self.set("first_run", False)
