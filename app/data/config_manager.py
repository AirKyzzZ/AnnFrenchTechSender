import json
import os
from app.data.models import Settings

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "config.json")


class ConfigManager:
    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

    def save(self, settings: Settings) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self) -> Settings:
        if not os.path.exists(self.config_path):
            return Settings()
        with open(self.config_path, "r", encoding="utf-8") as f:
            return Settings.from_dict(json.load(f))
