"""
database.py - Gestionnaire de base de donnees SQLite

Ce module centralise toutes les operations avec la base de donnees SQLite.
On utilise SQLite car c'est une base relationnelle legere, integree a Python
(module sqlite3 dans la stdlib), parfaite pour une application desktop mono-utilisateur.

Tables :
  - users        : comptes utilisateurs (login local avec mot de passe hashe)
  - profiles     : profils de candidature (1 profil par utilisateur)
  - historique   : historique des envois (permet de ne pas reenvoyer 2 fois)

Pourquoi SQLite et pas un fichier JSON pour tout ?
  → SQLite gere les relations entre tables (user_id → profils, historique)
  → Les requetes SQL permettent de filtrer/trier efficacement
  → Les transactions garantissent l'integrite des donnees
  (La blacklist et la config restent en JSON/TXT = approche NoSQL pour le jury)
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# Chemin par defaut de la base de donnees, a cote du dossier data/
# On utilise os.path pour construire un chemin portable (Windows/Mac/Linux)
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "ftsender.db")


class Database:
    """
    Classe qui gere la connexion et les operations SQLite.

    Utilise le pattern Singleton simplifie : une seule instance de connexion
    est partagee dans toute l'application pour eviter les conflits d'acces.
    """

    def __init__(self, db_path: str = DB_PATH):
        """
        Initialise la connexion a la base de donnees.

        Args:
            db_path: chemin vers le fichier .db (cree automatiquement s'il n'existe pas)
        """
        self.db_path = db_path

        # Creer le dossier parent si necessaire
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Ouvrir la connexion SQLite
        # check_same_thread=False permet d'utiliser la connexion depuis plusieurs threads
        # (necessaire car le sender tourne dans un thread separe)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)

        # row_factory = sqlite3.Row permet d'acceder aux colonnes par nom
        # au lieu de par index (ex: row["username"] au lieu de row[1])
        self.conn.row_factory = sqlite3.Row

        # Activer les cles etrangeres (desactivees par defaut dans SQLite)
        # Sans ca, les FOREIGN KEY ne sont pas verifiees
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Creer les tables si elles n'existent pas encore
        self._creer_tables()

        logger.info(f"Base de donnees initialisee: {self.db_path}")

    def _creer_tables(self):
        """
        Cree les tables SQL si elles n'existent pas.

        IF NOT EXISTS evite une erreur si les tables existent deja
        (utile au 2eme lancement de l'application).
        """
        curseur = self.conn.cursor()

        # Table des utilisateurs
        # - username est UNIQUE : pas de doublons possibles
        # - password_hash stocke le hash bcrypt (jamais le mot de passe en clair !)
        # - datetime('now') insere automatiquement la date de creation
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # Table des profils de candidature
        # - Chaque profil est lie a un utilisateur via user_id (cle etrangere)
        # - UNIQUE(user_id) : un seul profil par utilisateur (on peut l'etendre plus tard)
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                nom TEXT DEFAULT '',
                prenom TEXT DEFAULT '',
                email TEXT DEFAULT '',
                telephone TEXT DEFAULT '',
                objet TEXT DEFAULT '',
                message TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Table de l'historique des envois
        # - Enregistre chaque tentative d'envoi (succes ou echec)
        # - Permet de savoir quelles entreprises ont deja ete contactees
        # - statut : 'succes' ou 'echec' pour le suivi
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS historique (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                organisation TEXT DEFAULT '',
                statut TEXT NOT NULL,
                tentatives INTEGER DEFAULT 1,
                date_envoi TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Valider la creation des tables
        self.conn.commit()

    def executer(self, requete: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute une requete SQL avec des parametres.

        On utilise des parametres (?) au lieu de f-strings pour eviter
        les injections SQL (faille de securite critique).

        Exemple DANGEREUX : f"SELECT * FROM users WHERE username = '{nom}'"
        → Un attaquant pourrait envoyer: ' OR 1=1 --
        Exemple SECURISE  : "SELECT * FROM users WHERE username = ?", (nom,)
        → Le ? est remplace de maniere securisee par sqlite3

        Args:
            requete: la requete SQL avec des ? pour les parametres
            params: tuple de valeurs a inserer a la place des ?

        Returns:
            Le curseur SQLite (permet de lire les resultats)
        """
        return self.conn.execute(requete, params)

    def commit(self):
        """Valide les modifications en base (INSERT, UPDATE, DELETE)."""
        self.conn.commit()

    def fermer(self):
        """Ferme proprement la connexion a la base de donnees."""
        if self.conn:
            self.conn.close()
            logger.info("Connexion a la base de donnees fermee")
