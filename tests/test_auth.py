"""
Tests unitaires pour l'authentification (auth_manager.py).

Ces tests verifient que :
  - L'inscription cree un utilisateur avec un mot de passe hashe
  - La connexion fonctionne avec le bon mot de passe
  - La connexion echoue avec un mauvais mot de passe
  - Les validations (champs vides, doublons) fonctionnent
  - Le mot de passe n'est jamais stocke en clair
"""

import pytest
from app.data.database import Database
from app.data.auth_manager import AuthManager


@pytest.fixture
def auth(tmp_path):
    """Fixture : cree un AuthManager avec une base temporaire."""
    db = Database(str(tmp_path / "test.db"))
    manager = AuthManager(db)
    yield manager
    db.fermer()


class TestInscription:
    """Tests pour la fonctionnalite d'inscription."""

    def test_inscription_reussie(self, auth):
        """L'inscription avec des identifiants valides reussit."""
        succes, message = auth.inscrire("maxime", "monmdp123")
        assert succes is True
        assert "reussie" in message.lower()

    def test_inscription_username_vide(self, auth):
        """L'inscription echoue si le nom d'utilisateur est vide."""
        succes, message = auth.inscrire("", "monmdp123")
        assert succes is False
        assert "vide" in message.lower()

    def test_inscription_username_espaces(self, auth):
        """L'inscription echoue si le nom d'utilisateur est que des espaces."""
        succes, message = auth.inscrire("   ", "monmdp123")
        assert succes is False

    def test_inscription_mdp_trop_court(self, auth):
        """L'inscription echoue si le mot de passe fait moins de 4 caracteres."""
        succes, message = auth.inscrire("maxime", "abc")
        assert succes is False
        assert "4 caracteres" in message

    def test_inscription_doublon(self, auth):
        """L'inscription echoue si le nom d'utilisateur existe deja."""
        auth.inscrire("maxime", "monmdp123")
        succes, message = auth.inscrire("maxime", "autremdp")
        assert succes is False
        assert "existe deja" in message.lower()

    def test_mdp_jamais_en_clair(self, auth):
        """Le mot de passe n'est jamais stocke en clair dans la base."""
        auth.inscrire("maxime", "secret123")
        result = auth.db.executer(
            "SELECT password_hash FROM users WHERE username = ?", ("maxime",)
        ).fetchone()

        # Le hash ne doit PAS etre le mot de passe en clair
        assert result["password_hash"] != "secret123"
        # Le hash bcrypt commence toujours par $2b$
        assert result["password_hash"].startswith("$2b$")


class TestConnexion:
    """Tests pour la fonctionnalite de connexion."""

    def test_connexion_reussie(self, auth):
        """La connexion reussit avec les bons identifiants."""
        auth.inscrire("maxime", "monmdp123")
        succes, user_id, message = auth.connecter("maxime", "monmdp123")
        assert succes is True
        assert user_id is not None
        assert user_id > 0

    def test_connexion_mauvais_mdp(self, auth):
        """La connexion echoue avec un mauvais mot de passe."""
        auth.inscrire("maxime", "monmdp123")
        succes, user_id, message = auth.connecter("maxime", "mauvaismdp")
        assert succes is False
        assert user_id is None

    def test_connexion_utilisateur_inexistant(self, auth):
        """La connexion echoue si l'utilisateur n'existe pas."""
        succes, user_id, message = auth.connecter("inconnu", "monmdp123")
        assert succes is False
        assert user_id is None

    def test_connexion_champs_vides(self, auth):
        """La connexion echoue si les champs sont vides."""
        succes, user_id, message = auth.connecter("", "")
        assert succes is False
        assert "remplir" in message.lower()

    def test_message_erreur_generique(self, auth):
        """Le message d'erreur ne revele pas si c'est le username ou le mdp qui est faux."""
        auth.inscrire("maxime", "monmdp123")

        # Mauvais mot de passe
        _, _, msg1 = auth.connecter("maxime", "mauvais")
        # Utilisateur inexistant
        _, _, msg2 = auth.connecter("inconnu", "monmdp123")

        # Les deux messages doivent etre identiques (securite)
        # Empeche un attaquant de deviner quels usernames existent
        assert msg1 == msg2


class TestUtilitaires:
    """Tests pour les methodes utilitaires."""

    def test_utilisateur_existe(self, auth):
        """utilisateur_existe() retourne True pour un utilisateur inscrit."""
        auth.inscrire("maxime", "monmdp123")
        assert auth.utilisateur_existe("maxime") is True

    def test_utilisateur_nexiste_pas(self, auth):
        """utilisateur_existe() retourne False pour un utilisateur inexistant."""
        assert auth.utilisateur_existe("inconnu") is False

    def test_get_username(self, auth):
        """get_username() retourne le nom d'utilisateur a partir de l'id."""
        auth.inscrire("maxime", "monmdp123")
        _, user_id, _ = auth.connecter("maxime", "monmdp123")
        assert auth.get_username(user_id) == "maxime"

    def test_get_username_inexistant(self, auth):
        """get_username() retourne None pour un id inexistant."""
        assert auth.get_username(9999) is None
