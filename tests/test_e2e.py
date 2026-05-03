"""
Tests End-to-End (E2E) - Simulation du parcours complet.

Ces tests simulent un envoi de candidature complet SANS ouvrir Chrome.
On utilise unittest.mock pour "simuler" Selenium (mock = objet factice
qui imite le comportement reel sans executer le code).

Pourquoi mocker Selenium ?
  → Les tests doivent etre rapides (pas d'attente de 240s pour l'anti-bot)
  → Pas besoin de Chrome installe sur la machine de test (CI/CD)
  → On controle le comportement du "navigateur" pour tester tous les cas

Le parcours teste :
  1. Inscription d'un utilisateur
  2. Connexion
  3. Creation du profil
  4. Envoi de candidatures (mock Selenium)
  5. Verification de l'historique
"""

import csv
import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from app.data.database import Database
from app.data.auth_manager import AuthManager
from app.data.profile_manager import ProfileManager
from app.data.history_manager import HistoryManager
from app.data.blacklist_manager import BlacklistManager
from app.data.config_manager import ConfigManager
from app.data.models import UserProfile, Settings
from app.core.sender_engine import SenderEngine


@pytest.fixture
def setup_complet(tmp_path):
    """
    Fixture E2E : cree toute l'infrastructure necessaire.

    Retourne un dictionnaire avec tous les managers initialises
    et un utilisateur deja inscrit et connecte.
    """
    db = Database(str(tmp_path / "e2e.db"))
    auth = AuthManager(db)

    # Inscrire et connecter un utilisateur
    auth.inscrire("maxime", "testpass123")
    _, user_id, _ = auth.connecter("maxime", "testpass123")

    # Creer un profil complet
    pm = ProfileManager(db, user_id)
    profile = UserProfile(
        nom="Mansiet", prenom="Maxime",
        email="maxime@epsi.fr", telephone="0600000000",
        objet="Candidature de stage", message="Bonjour, je suis en BTS SIO..."
    )
    pm.save(profile)

    # Creer un fichier CSV de test avec 3 URLs
    csv_path = str(tmp_path / "urls.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["URL"])
        writer.writerow(["https://ftb.com/organisations/entreprise-a"])
        writer.writerow(["https://ftb.com/organisations/entreprise-b"])
        writer.writerow(["https://ftb.com/organisations/entreprise-c"])

    # Creer une blacklist vide
    bl_path = str(tmp_path / "blacklist.txt")
    bl = BlacklistManager(bl_path)

    # Creer les settings
    settings = Settings(
        csv_path=csv_path,
        blacklist_path=bl_path,
        delay_min=0.01,  # Delais minimaux pour les tests
        delay_max=0.02,
        timeout_bouton=5,
        max_tentatives=2,
    )

    hm = HistoryManager(db, user_id)

    yield {
        "db": db,
        "auth": auth,
        "profile_manager": pm,
        "history_manager": hm,
        "blacklist": bl,
        "profile": profile,
        "settings": settings,
        "user_id": user_id,
        "csv_path": csv_path,
        "tmp_path": tmp_path,
    }

    db.fermer()


def _creer_mock_driver():
    """
    Cree un faux driver Selenium qui simule un envoi reussi.

    Le mock imite le comportement de Chrome :
      - find_element() retourne un element factice
      - Le bouton submit a une valeur "Envoyer" et n'est pas disabled
      - Le texte de la page contient "Votre message a bien" (confirmation)
    """
    driver = MagicMock()

    # Simuler les elements du formulaire
    # Chaque find_element retourne un MagicMock qui accepte send_keys()
    mock_element = MagicMock()
    driver.find_element.return_value = mock_element

    # Simuler le bouton submit actif
    mock_submit = MagicMock()
    mock_submit.get_attribute.side_effect = lambda attr: {
        "value": "Envoyer le message",
        "disabled": None,  # None = pas disabled = bouton actif
    }.get(attr)

    # Simuler le body avec le message de confirmation
    mock_body = MagicMock()
    mock_body.text = "Votre message a bien ete envoye"

    def find_element_side_effect(by, value):
        if value == "//input[@type='submit']":
            return mock_submit
        if value == "body":
            return mock_body
        return MagicMock()  # Elements de formulaire generiques

    driver.find_element.side_effect = find_element_side_effect
    return driver


class TestE2EEnvoiComplet:
    """
    Test E2E : simule un envoi complet de candidatures.

    Ce test verifie le parcours de bout en bout :
    inscription → connexion → profil → envoi → historique.
    """

    @patch("app.core.sender_engine.time.sleep")
    @patch("app.core.sender_engine.SeleniumManager")
    def test_envoi_3_candidatures_succes(self, MockSeleniumManager, mock_sleep, setup_complet):
        """
        Simule l'envoi de 3 candidatures avec succes.

        On mock SeleniumManager pour eviter d'ouvrir Chrome.
        On mock time.sleep pour accelerer les tests (pas de delai reel).
        Le mock simule un navigateur qui remplit le formulaire et recoit
        un message de confirmation a chaque fois.
        """
        ctx = setup_complet

        # Configurer le mock de SeleniumManager
        mock_selenium_instance = MagicMock()
        mock_selenium_instance.get_driver.return_value = _creer_mock_driver()
        mock_selenium_instance.session_expiree.return_value = False
        MockSeleniumManager.return_value = mock_selenium_instance

        # Creer et lancer le moteur d'envoi
        engine = SenderEngine()
        engine.start(ctx["profile"], ctx["settings"], ctx["history_manager"], dry_run=False)

        # Attendre la fin de l'envoi (max 15 secondes)
        timeout = time.time() + 15
        while engine.state != "idle" and time.time() < timeout:
            time.sleep(0.1)

        assert engine.state == "idle", "Le moteur n'a pas termine a temps"

        # Verifier les statistiques
        stats = engine.stats
        assert stats.envoyes == 3
        assert stats.echecs == 0

        # Verifier l'historique dans SQLite
        hist = ctx["history_manager"].get_historique()
        assert len(hist) == 3
        assert all(h["statut"] == "succes" for h in hist)

        # Verifier les statistiques depuis l'historique
        counts = ctx["history_manager"].compter_envois()
        assert counts["succes"] == 3
        assert counts["echecs"] == 0

    def test_envoi_dry_run(self, setup_complet):
        """
        Le mode test (dry_run) simule l'envoi sans ouvrir Chrome.

        Pas besoin de mock ici : dry_run=True n'utilise pas Selenium du tout.
        Mais les envois en dry_run ne sont PAS enregistres dans l'historique
        (car ce n'est pas un vrai envoi).
        """
        ctx = setup_complet

        engine = SenderEngine()
        engine.start(ctx["profile"], ctx["settings"], ctx["history_manager"], dry_run=True)

        timeout = time.time() + 10
        while engine.state != "idle" and time.time() < timeout:
            time.sleep(0.1)

        assert engine.state == "idle"
        assert engine.stats.envoyes == 3
        assert engine.stats.echecs == 0

    @patch("app.core.sender_engine.time.sleep")
    @patch("app.core.sender_engine.SeleniumManager")
    def test_envoi_ne_refait_pas_les_deja_envoyes(self, MockSeleniumManager, mock_sleep, setup_complet):
        """
        Les URLs deja envoyees avec succes sont ignorees au 2eme lancement.

        C'est la fonctionnalite cle : on peut arreter et relancer le programme
        sans reenvoyer aux memes entreprises.
        """
        ctx = setup_complet

        mock_selenium_instance = MagicMock()
        mock_selenium_instance.get_driver.return_value = _creer_mock_driver()
        mock_selenium_instance.session_expiree.return_value = False
        MockSeleniumManager.return_value = mock_selenium_instance

        # Premier envoi : 3 URLs
        engine1 = SenderEngine()
        engine1.start(ctx["profile"], ctx["settings"], ctx["history_manager"], dry_run=False)
        timeout = time.time() + 15
        while engine1.state != "idle" and time.time() < timeout:
            time.sleep(0.1)
        assert engine1.stats.envoyes == 3

        # Deuxieme envoi : 0 URL (toutes deja envoyees)
        engine2 = SenderEngine()
        engine2.start(ctx["profile"], ctx["settings"], ctx["history_manager"], dry_run=False)
        timeout = time.time() + 15
        while engine2.state != "idle" and time.time() < timeout:
            time.sleep(0.1)
        assert engine2.stats.total == 0  # Aucune URL a traiter


class TestE2EAvecBlacklist:
    """Test E2E : interaction entre blacklist et envoi."""

    @patch("app.core.sender_engine.time.sleep")
    @patch("app.core.sender_engine.SeleniumManager")
    def test_blacklist_exclut_urls(self, MockSeleniumManager, mock_sleep, setup_complet):
        """Les URLs en blacklist sont exclues de l'envoi."""
        ctx = setup_complet

        # Blacklister une des 3 entreprises
        ctx["blacklist"].add("https://ftb.com/organisations/entreprise-b")

        mock_selenium_instance = MagicMock()
        mock_selenium_instance.get_driver.return_value = _creer_mock_driver()
        mock_selenium_instance.session_expiree.return_value = False
        MockSeleniumManager.return_value = mock_selenium_instance

        engine = SenderEngine()
        engine.start(ctx["profile"], ctx["settings"], ctx["history_manager"], dry_run=False)

        timeout = time.time() + 15
        while engine.state != "idle" and time.time() < timeout:
            time.sleep(0.1)

        # 2 envois seulement (entreprise-b est blacklistee)
        assert engine.stats.envoyes == 2
        assert engine.stats.total == 2


class TestE2EControleEnvoi:
    """Test E2E : controle de l'envoi (pause, arret)."""

    def test_arret_en_cours_envoi(self, setup_complet):
        """
        L'arret pendant l'envoi stoppe proprement le moteur.

        On utilise dry_run avec des delais courts pour pouvoir
        interrompre pendant le traitement.
        """
        ctx = setup_complet

        # Augmenter les delais pour avoir le temps d'arreter
        ctx["settings"].delay_min = 0.5
        ctx["settings"].delay_max = 1.0

        engine = SenderEngine()
        engine.start(ctx["profile"], ctx["settings"], ctx["history_manager"], dry_run=True)

        # Attendre que le premier envoi commence
        time.sleep(0.3)

        # Arreter
        engine.stop()

        # Attendre que le moteur s'arrete
        timeout = time.time() + 5
        while engine.state not in ("idle", "stopped") and time.time() < timeout:
            time.sleep(0.1)

        # Moins de 3 envois (arrete en cours)
        assert engine.stats.envoyes < 3
