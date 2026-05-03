"""
Tests unitaires pour les modeles de donnees (models.py).

Ces tests verifient que les dataclasses fonctionnent correctement :
  - Creation avec valeurs par defaut
  - Serialisation vers/depuis un dictionnaire
  - Validation des champs
  - Calcul des statistiques
"""

import pytest
from app.data.models import User, UserProfile, Settings, SendingStats


# ============================================================
# Tests du modele User
# ============================================================

class TestUser:
    """Tests pour le modele User."""

    def test_creation_par_defaut(self):
        """Un User cree sans arguments a des valeurs par defaut."""
        user = User()
        assert user.id == 0
        assert user.username == ""

    def test_creation_avec_valeurs(self):
        """Un User cree avec des arguments les stocke correctement."""
        user = User(id=1, username="maxime")
        assert user.id == 1
        assert user.username == "maxime"


# ============================================================
# Tests du modele UserProfile
# ============================================================

class TestUserProfile:
    """Tests pour le modele UserProfile."""

    def test_creation_par_defaut(self):
        """Un profil vide a tous ses champs a vide."""
        profile = UserProfile()
        assert profile.nom == ""
        assert profile.email == ""
        assert profile.message == ""

    def test_creation_avec_valeurs(self):
        """Un profil avec des valeurs les stocke correctement."""
        profile = UserProfile(
            nom="Mansiet", prenom="Maxime",
            email="max@test.com", telephone="0600000000",
            objet="Stage", message="Bonjour"
        )
        assert profile.nom == "Mansiet"
        assert profile.prenom == "Maxime"
        assert profile.email == "max@test.com"

    def test_to_dict(self):
        """to_dict() retourne un dictionnaire avec tous les champs."""
        profile = UserProfile(nom="Test", prenom="User", email="t@t.com",
                              telephone="01", objet="Obj", message="Msg")
        d = profile.to_dict()
        assert d["nom"] == "Test"
        assert d["email"] == "t@t.com"
        assert len(d) == 6  # 6 champs

    def test_from_dict(self):
        """from_dict() cree un profil depuis un dictionnaire."""
        data = {"nom": "Test", "prenom": "User", "email": "t@t.com",
                "telephone": "01", "objet": "Obj", "message": "Msg"}
        profile = UserProfile.from_dict(data)
        assert profile.nom == "Test"
        assert profile.email == "t@t.com"

    def test_from_dict_ignore_champs_inconnus(self):
        """from_dict() ignore les cles qui ne sont pas des champs du modele."""
        data = {"nom": "Test", "champ_inconnu": "valeur", "prenom": "X",
                "email": "", "telephone": "", "objet": "", "message": ""}
        profile = UserProfile.from_dict(data)
        assert profile.nom == "Test"
        assert not hasattr(profile, "champ_inconnu")

    def test_is_valid_profil_complet(self):
        """is_valid() retourne True si tous les champs obligatoires sont remplis."""
        profile = UserProfile(nom="A", prenom="B", email="c@d.com",
                              telephone="01", objet="Obj", message="Msg")
        assert profile.is_valid() is True

    def test_is_valid_profil_incomplet(self):
        """is_valid() retourne False si un champ obligatoire est vide."""
        profile = UserProfile(nom="A", prenom="B", email="",
                              telephone="01", objet="Obj", message="Msg")
        assert profile.is_valid() is False

    def test_is_valid_profil_vide(self):
        """is_valid() retourne False pour un profil entierement vide."""
        profile = UserProfile()
        assert profile.is_valid() is False


# ============================================================
# Tests du modele Settings
# ============================================================

class TestSettings:
    """Tests pour le modele Settings."""

    def test_valeurs_par_defaut(self):
        """Les parametres par defaut sont raisonnables."""
        settings = Settings()
        assert settings.delay_min == 2.0
        assert settings.delay_max == 5.0
        assert settings.headless is True
        assert settings.csv_path == "urls_entreprises.csv"

    def test_to_dict(self):
        """to_dict() retourne tous les parametres."""
        settings = Settings()
        d = settings.to_dict()
        assert "delay_min" in d
        assert "headless" in d
        assert d["delay_min"] == 2.0

    def test_from_dict(self):
        """from_dict() charge des parametres personnalises."""
        data = {"delay_min": 1.0, "headless": False}
        settings = Settings.from_dict(data)
        assert settings.delay_min == 1.0
        assert settings.headless is False
        # Les champs non fournis gardent leur valeur par defaut
        assert settings.delay_max == 5.0


# ============================================================
# Tests du modele SendingStats
# ============================================================

class TestSendingStats:
    """Tests pour le modele SendingStats."""

    def test_valeurs_par_defaut(self):
        """Les stats demarrent a zero."""
        stats = SendingStats()
        assert stats.total == 0
        assert stats.envoyes == 0
        assert stats.echecs == 0

    def test_taux_reussite_zero_division(self):
        """Le taux est 0% quand aucune candidature n'a ete traitee."""
        stats = SendingStats()
        assert stats.taux_reussite == 0.0

    def test_taux_reussite_calcul(self):
        """Le taux se calcule correctement : (envoyes / traites) * 100."""
        stats = SendingStats(envoyes=7, echecs=3)
        assert stats.taux_reussite == 70.0

    def test_taux_reussite_100(self):
        """100% quand tout a reussi."""
        stats = SendingStats(envoyes=10, echecs=0)
        assert stats.taux_reussite == 100.0

    def test_traites(self):
        """traites = envoyes + echecs."""
        stats = SendingStats(envoyes=5, echecs=3)
        assert stats.traites == 8

    def test_to_dict_inclut_proprietes(self):
        """to_dict() inclut les proprietes calculees (taux, traites)."""
        stats = SendingStats(total=10, envoyes=7, echecs=3)
        d = stats.to_dict()
        assert d["taux_reussite"] == 70.0
        assert d["traites"] == 10
