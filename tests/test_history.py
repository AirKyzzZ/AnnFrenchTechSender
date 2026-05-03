"""
Tests unitaires pour le gestionnaire d'historique (history_manager.py).

Ces tests verifient que :
  - Les envois sont enregistres correctement dans SQLite
  - La detection de doublons fonctionne (deja_envoye)
  - Les statistiques sont calculees correctement
  - L'historique est filtre par utilisateur
"""

import pytest
from app.data.database import Database
from app.data.history_manager import HistoryManager


@pytest.fixture
def db(tmp_path):
    """Fixture : base de donnees temporaire."""
    database = Database(str(tmp_path / "test.db"))
    yield database
    database.fermer()


@pytest.fixture
def history(db):
    """Fixture : HistoryManager pour l'utilisateur 1."""
    # Creer un utilisateur de test
    db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("testuser", "hash"))
    db.commit()
    user = db.executer("SELECT id FROM users WHERE username = ?", ("testuser",)).fetchone()
    return HistoryManager(db, user["id"])


class TestEnregistrement:
    """Tests pour l'enregistrement des envois."""

    def test_enregistrer_succes(self, history):
        """Un envoi reussi est enregistre avec le statut 'succes'."""
        history.enregistrer_envoi("https://example.com/organisations/org1", "succes")
        hist = history.get_historique()
        assert len(hist) == 1
        assert hist[0]["statut"] == "succes"
        assert hist[0]["organisation"] == "org1"

    def test_enregistrer_echec(self, history):
        """Un envoi echoue est enregistre avec le statut 'echec'."""
        history.enregistrer_envoi("https://example.com/organisations/org1", "echec", tentatives=3)
        hist = history.get_historique()
        assert len(hist) == 1
        assert hist[0]["statut"] == "echec"
        assert hist[0]["tentatives"] == 3

    def test_enregistrer_plusieurs(self, history):
        """On peut enregistrer plusieurs envois."""
        history.enregistrer_envoi("https://example.com/organisations/org1", "succes")
        history.enregistrer_envoi("https://example.com/organisations/org2", "echec")
        history.enregistrer_envoi("https://example.com/organisations/org3", "succes")
        hist = history.get_historique()
        assert len(hist) == 3


class TestDetectionDoublons:
    """Tests pour la detection des URLs deja envoyees."""

    def test_deja_envoye_succes(self, history):
        """deja_envoye() retourne True si l'URL a ete envoyee avec succes."""
        history.enregistrer_envoi("https://example.com/organisations/org1", "succes")
        assert history.deja_envoye("https://example.com/organisations/org1") is True

    def test_pas_deja_envoye(self, history):
        """deja_envoye() retourne False pour une URL inconnue."""
        assert history.deja_envoye("https://example.com/organisations/inconnu") is False

    def test_echec_pas_considere_comme_envoye(self, history):
        """deja_envoye() retourne False si l'envoi a echoue (on peut retenter)."""
        history.enregistrer_envoi("https://example.com/organisations/org1", "echec")
        assert history.deja_envoye("https://example.com/organisations/org1") is False

    def test_get_urls_envoyees(self, history):
        """get_urls_envoyees() retourne un set des URLs envoyees avec succes."""
        history.enregistrer_envoi("https://example.com/organisations/org1", "succes")
        history.enregistrer_envoi("https://example.com/organisations/org2", "echec")
        history.enregistrer_envoi("https://example.com/organisations/org3", "succes")

        urls = history.get_urls_envoyees()
        assert len(urls) == 2
        assert "https://example.com/organisations/org1" in urls
        assert "https://example.com/organisations/org3" in urls
        # org2 a echoue, elle ne doit pas etre dans le set
        assert "https://example.com/organisations/org2" not in urls


class TestStatistiques:
    """Tests pour le calcul des statistiques."""

    def test_stats_vides(self, history):
        """Les stats sont a zero quand il n'y a pas d'historique."""
        stats = history.compter_envois()
        assert stats["total"] == 0
        assert stats["succes"] == 0
        assert stats["echecs"] == 0

    def test_stats_calcul(self, history):
        """Les stats comptent correctement les succes et echecs."""
        history.enregistrer_envoi("https://example.com/org1", "succes")
        history.enregistrer_envoi("https://example.com/org2", "succes")
        history.enregistrer_envoi("https://example.com/org3", "echec")

        stats = history.compter_envois()
        assert stats["total"] == 3
        assert stats["succes"] == 2
        assert stats["echecs"] == 1


class TestIsolationUtilisateurs:
    """Tests pour verifier que les donnees sont isolees par utilisateur."""

    def test_historique_isole(self, db):
        """Chaque utilisateur ne voit que son propre historique."""
        # Creer deux utilisateurs
        db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("user1", "h1"))
        db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("user2", "h2"))
        db.commit()

        u1 = db.executer("SELECT id FROM users WHERE username = ?", ("user1",)).fetchone()
        u2 = db.executer("SELECT id FROM users WHERE username = ?", ("user2",)).fetchone()

        # Enregistrer des envois pour chaque utilisateur
        hm1 = HistoryManager(db, u1["id"])
        hm2 = HistoryManager(db, u2["id"])

        hm1.enregistrer_envoi("https://example.com/org1", "succes")
        hm1.enregistrer_envoi("https://example.com/org2", "succes")
        hm2.enregistrer_envoi("https://example.com/org3", "succes")

        # Verifier l'isolation
        assert len(hm1.get_historique()) == 2
        assert len(hm2.get_historique()) == 1
        assert hm1.deja_envoye("https://example.com/org3") is False
        assert hm2.deja_envoye("https://example.com/org1") is False
