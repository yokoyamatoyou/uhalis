import json
import os

CONFIG_FILE = 'config.json'
MODEL_NAME = "gpt-4.1-mini-2025-04-14"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_TOP_P = 0.9

DEFAULT_WEIGHTS = {
    "hate_score": 0.06,
    "hate/threatening_score": 0.04,
    "violence_score": 0.04,
    "sexual_score": 0.02,
    "sexual/minors_score": 0.02,
    "aggressiveness_score": 0.06,
    "flag_hate": 0.28,
    "flag_hate/threatening": 0.14,
    "flag_violence": 0.20,
    "flag_sexual": 0.14
}

class ConfigManager:
    """Handle reading and writing of configuration values."""

    def __init__(self, path: str = CONFIG_FILE):
        """Initialize the manager and load the config file."""
        self.path = path
        self.data: dict = {}
        self.load()

    def load(self):
        """Load configuration from ``self.path`` if it exists."""
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "weights": DEFAULT_WEIGHTS.copy(),
                "temperature": DEFAULT_TEMPERATURE,
                "top_p": DEFAULT_TOP_P,
            }

    def save(self):
        """Persist current settings to disk."""
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_weight(self, key: str) -> float:
        """Return a weight value from the config."""
        return self.data.get("weights", {}).get(key, DEFAULT_WEIGHTS.get(key, 0.0))

    def set_weight(self, key: str, value: float):
        """Update a weight entry and ensure the section exists."""
        if "weights" not in self.data:
            self.data["weights"] = {}
        self.data["weights"][key] = value

    def get_temperature(self) -> float:
        """Return the saved temperature setting."""
        return float(self.data.get("temperature", DEFAULT_TEMPERATURE))

    def set_temperature(self, value: float):
        """Set and store the temperature value."""
        self.data["temperature"] = value

    def get_top_p(self) -> float:
        """Return the saved top-p setting."""
        return float(self.data.get("top_p", DEFAULT_TOP_P))

    def set_top_p(self, value: float):
        """Set and store the top-p value."""
        self.data["top_p"] = value
