import json
import os
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.glint_dir = Path.home() / ".glint"
        self.config_path = self.glint_dir / "config.json"
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Ensure config directory and file exist."""
        if not self.glint_dir.exists():
            self.glint_dir.mkdir(parents=True, exist_ok=True)
            
        if not self.config_path.exists():
            default_config = {
                "api_keys": {
                    "producthunt": "",
                    "devto": "",
                    "reddit_client_id": "",
                    "reddit_secret": ""
                },
                "settings": {
                    "theme": "Dark"
                }
            }
            self._save_to_file(default_config)

    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_to_file(self, config: Dict[str, Any]):
        """Save configuration to JSON file."""
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)

    def get_secret(self, key: str) -> str:
        """Get an API key or secret."""
        config = self._load_from_file()
        return config.get("api_keys", {}).get(key, "")

    def set_secret(self, key: str, value: str):
        """Set an API key or secret."""
        config = self._load_from_file()
        if "api_keys" not in config:
            config["api_keys"] = {}
        config["api_keys"][key] = value
        self._save_to_file(config)

    def get_all_secrets(self) -> Dict[str, str]:
        """Get all secrets (for display)."""
        config = self._load_from_file()
        return config.get("api_keys", {})

# Global instance
config_manager = ConfigManager()
