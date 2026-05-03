"""
config_manager.py - Gestionnaire de la configuration

La configuration est stockee en JSON (fichier config.json).
C'est la deuxieme approche "NoSQL" du projet (avec la blacklist en TXT) :
un fichier JSON est un format de donnees non-relationnel.

Pourquoi JSON pour la config ?
  → La config est un ensemble de paires cle/valeur sans relations
  → JSON est lisible par un humain et editable manuellement
  → Pas besoin de requetes SQL pour de la simple configuration
"""

import json
import os
from app.data.models import Settings

# Chemin par defaut du fichier de configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "config.json")


class ConfigManager:
    """
    Sauvegarde et charge les parametres de l'application en JSON.

    Les parametres incluent : delais entre envois, timeouts,
    mode headless, chemins de fichiers, etc.
    """

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
