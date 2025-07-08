import json
import os

CONFIG_FILE = 'config.json'
MODEL_NAME = "gpt-4.1-mini-2025-04-14"

DEFAULT_WEIGHTS = {
    "hate_score": 0.5,
    "hate/threatening_score": 0.3,
    "violence_score": 0.3,
    "sexual_score": 0.1,
    "sexual/minors_score": 0.1,
    "aggressiveness_score": 0.5,
    "flag_hate": 2.0,
    "flag_hate/threatening": 1.0,
    "flag_violence": 1.5,
    "flag_sexual": 1.0
}

class ConfigManager:
    def __init__(self, path: str = CONFIG_FILE):
        self.path = path
        self.data: dict = {}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {"weights": DEFAULT_WEIGHTS.copy()}

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_weight(self, key: str) -> float:
        return self.data.get("weights", {}).get(key, DEFAULT_WEIGHTS.get(key, 0.0))

    def set_weight(self, key: str, value: float):
        if "weights" not in self.data:
            self.data["weights"] = {}
        self.data["weights"][key] = value
