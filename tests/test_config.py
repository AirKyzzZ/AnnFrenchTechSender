"""
Tests unitaires pour le gestionnaire de configuration (config_manager.py).

La configuration est stockee en JSON (approche NoSQL) car c'est une
structure simple sans relations. Ces tests verifient la lecture/ecriture.
"""

import pytest
from app.data.config_manager import ConfigManager
from app.data.models import Settings


@pytest.fixture
def config(tmp_path):
    """Fixture : ConfigManager avec un fichier temporaire."""
    config_path = str(tmp_path / "config.json")
    return ConfigManager(config_path)


class TestConfig:
    """Tests pour le ConfigManager."""

    def test_load_defaut(self, config):
        """Si le fichier n'existe pas, les parametres par defaut sont retournes."""
        settings = config.load()
        assert settings.delay_min == 2.0
        assert settings.headless is True

    def test_save_et_load(self, config):
        """Les parametres sauvegardes sont retrouves au chargement."""
        settings = Settings(delay_min=1.0, delay_max=3.0, headless=False)
        config.save(settings)

        loaded = config.load()
        assert loaded.delay_min == 1.0
        assert loaded.delay_max == 3.0
        assert loaded.headless is False

    def test_persistance(self, tmp_path):
        """Les donnees persistent entre deux instances de ConfigManager."""
        config_path = str(tmp_path / "config.json")

        # Premiere instance : sauvegarder
        cm1 = ConfigManager(config_path)
        cm1.save(Settings(timeout_page=60))

        # Deuxieme instance : charger
        cm2 = ConfigManager(config_path)
        settings = cm2.load()
        assert settings.timeout_page == 60

    def test_save_ne_perd_pas_les_champs(self, config):
        """Sauvegarder puis charger garde tous les champs."""
        settings = Settings(
            delay_min=1.5, delay_max=4.0, timeout_page=45,
            timeout_bouton=300, max_tentatives=3, headless=False,
            csv_path="custom.csv", blacklist_path="custom_bl.txt",
        )
        config.save(settings)
        loaded = config.load()

        assert loaded.delay_min == 1.5
        assert loaded.timeout_page == 45
        assert loaded.max_tentatives == 3
        assert loaded.csv_path == "custom.csv"
