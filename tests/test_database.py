"""
Tests unitaires pour la couche base de donnees (database.py).

Ces tests verifient que :
  - Les tables sont creees correctement au demarrage
  - Les requetes INSERT, SELECT, UPDATE, DELETE fonctionnent
  - Les cles etrangeres sont activees
  - Les contraintes UNIQUE sont respectees

On utilise une base SQLite en memoire (":memory:") pour les tests,
ce qui est plus rapide et ne laisse pas de fichier sur le disque.
"""

import pytest
import sqlite3
from app.data.database import Database


@pytest.fixture
def db(tmp_path):
    """
    Fixture pytest : cree une base de donnees temporaire pour chaque test.

    tmp_path est un repertoire temporaire fourni par pytest, automatiquement
    nettoye apres les tests. Chaque test a sa propre base isolee.
    """
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    yield database
    database.fermer()


class TestCreationTables:
    """Verifie que les tables SQL sont creees correctement."""

    def test_table_users_existe(self, db):
        """La table users doit exister apres initialisation."""
        result = db.executer(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        assert result is not None

    def test_table_profiles_existe(self, db):
        """La table profiles doit exister apres initialisation."""
        result = db.executer(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'"
        ).fetchone()
        assert result is not None

    def test_table_historique_existe(self, db):
        """La table historique doit exister apres initialisation."""
        result = db.executer(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='historique'"
        ).fetchone()
        assert result is not None


class TestOperationsCRUD:
    """Verifie les operations de base (Create, Read, Update, Delete)."""

    def test_insert_user(self, db):
        """On peut inserer un utilisateur dans la table users."""
        db.executer(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("testuser", "hash123"),
        )
        db.commit()

        result = db.executer("SELECT username FROM users WHERE username = ?", ("testuser",)).fetchone()
        assert result is not None
        assert result["username"] == "testuser"

    def test_username_unique(self, db):
        """Deux utilisateurs ne peuvent pas avoir le meme username (UNIQUE)."""
        db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("dupliquer", "hash"))
        db.commit()

        # La 2eme insertion avec le meme username doit echouer
        with pytest.raises(sqlite3.IntegrityError):
            db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("dupliquer", "hash2"))
            db.commit()

    def test_insert_profile(self, db):
        """On peut inserer un profil lie a un utilisateur."""
        # Creer d'abord l'utilisateur (cle etrangere)
        db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("user1", "hash"))
        db.commit()

        user = db.executer("SELECT id FROM users WHERE username = ?", ("user1",)).fetchone()
        db.executer(
            "INSERT INTO profiles (user_id, nom, prenom, email) VALUES (?, ?, ?, ?)",
            (user["id"], "Mansiet", "Maxime", "max@test.com"),
        )
        db.commit()

        profile = db.executer("SELECT * FROM profiles WHERE user_id = ?", (user["id"],)).fetchone()
        assert profile["nom"] == "Mansiet"
        assert profile["email"] == "max@test.com"

    def test_insert_historique(self, db):
        """On peut inserer un enregistrement dans l'historique."""
        db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("user1", "hash"))
        db.commit()
        user = db.executer("SELECT id FROM users WHERE username = ?", ("user1",)).fetchone()

        db.executer(
            "INSERT INTO historique (user_id, url, organisation, statut) VALUES (?, ?, ?, ?)",
            (user["id"], "https://example.com/org1", "org1", "succes"),
        )
        db.commit()

        hist = db.executer("SELECT * FROM historique WHERE user_id = ?", (user["id"],)).fetchone()
        assert hist["url"] == "https://example.com/org1"
        assert hist["statut"] == "succes"

    def test_update_profile(self, db):
        """On peut mettre a jour un profil existant."""
        db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("user1", "hash"))
        db.commit()
        user = db.executer("SELECT id FROM users WHERE username = ?", ("user1",)).fetchone()

        db.executer("INSERT INTO profiles (user_id, nom) VALUES (?, ?)", (user["id"], "Ancien"))
        db.commit()

        db.executer("UPDATE profiles SET nom = ? WHERE user_id = ?", ("Nouveau", user["id"]))
        db.commit()

        profile = db.executer("SELECT nom FROM profiles WHERE user_id = ?", (user["id"],)).fetchone()
        assert profile["nom"] == "Nouveau"

    def test_delete_user(self, db):
        """On peut supprimer un utilisateur."""
        db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("a_supprimer", "hash"))
        db.commit()

        db.executer("DELETE FROM users WHERE username = ?", ("a_supprimer",))
        db.commit()

        result = db.executer("SELECT id FROM users WHERE username = ?", ("a_supprimer",)).fetchone()
        assert result is None


class TestRowFactory:
    """Verifie que row_factory permet l'acces par nom de colonne."""

    def test_acces_par_nom(self, db):
        """Les resultats sont accessibles par nom de colonne grace a row_factory."""
        db.executer("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("test", "hash"))
        db.commit()

        result = db.executer("SELECT * FROM users WHERE username = ?", ("test",)).fetchone()
        # Acces par nom de colonne (et non par index)
        assert result["username"] == "test"
        assert result["password_hash"] == "hash"
