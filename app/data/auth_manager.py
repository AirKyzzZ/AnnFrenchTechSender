"""
auth_manager.py - Gestionnaire d'authentification locale

Ce module gere l'inscription et la connexion des utilisateurs.
Les mots de passe ne sont JAMAIS stockes en clair dans la base de donnees.
On utilise bcrypt pour les hasher avant de les enregistrer.

Pourquoi bcrypt ?
  → bcrypt ajoute un "sel" (salt) aleatoire a chaque hash automatiquement
  → Ca empeche les attaques par rainbow table (tables de hashes pre-calcules)
  → Le facteur de cout (12 rounds par defaut) rend le brute-force tres lent
  → C'est le standard de l'industrie pour le hachage de mots de passe
"""

import bcrypt
import logging
from app.data.database import Database

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Gere l'inscription et la connexion des utilisateurs.

    Toutes les operations de mot de passe passent par bcrypt :
      - Inscription : mot de passe → hash bcrypt → stocke en base
      - Connexion   : mot de passe saisi → compare au hash stocke via bcrypt.checkpw()
    """

    def __init__(self, db: Database):
        """
        Args:
            db: instance de Database pour acceder a la table users
        """
        self.db = db

    def inscrire(self, username: str, password: str) -> tuple[bool, str]:
        """
        Inscrit un nouvel utilisateur.

        Etapes :
          1. Verifier que le nom d'utilisateur n'est pas vide
          2. Verifier que le mot de passe fait au moins 4 caracteres
          3. Hasher le mot de passe avec bcrypt
          4. Inserer dans la table users

        Args:
            username: nom d'utilisateur choisi
            password: mot de passe en clair (sera hashe avant stockage)

        Returns:
            (succes: bool, message: str) - le message explique l'erreur si echec
        """
        # Validation des champs
        username = username.strip()
        if not username:
            return False, "Le nom d'utilisateur ne peut pas etre vide"

        if len(password) < 4:
            return False, "Le mot de passe doit faire au moins 4 caracteres"

        # Verifier si le nom d'utilisateur existe deja
        resultat = self.db.executer(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()

        if resultat:
            return False, "Ce nom d'utilisateur existe deja"

        # Hasher le mot de passe avec bcrypt
        # gensalt() genere un sel aleatoire (12 rounds par defaut)
        # hashpw() combine le sel + le mot de passe pour creer le hash
        # .encode() convertit le string en bytes (bcrypt travaille avec des bytes)
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Stocker le hash en base (decode() pour le stocker comme texte dans SQLite)
        try:
            self.db.executer(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash.decode("utf-8")),
            )
            self.db.commit()
            logger.info(f"Nouvel utilisateur inscrit: {username}")
            return True, "Inscription reussie"
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription: {e}")
            return False, "Erreur lors de l'inscription"

    def connecter(self, username: str, password: str) -> tuple[bool, int | None, str]:
        """
        Verifie les identifiants d'un utilisateur.

        Etapes :
          1. Chercher l'utilisateur dans la base par son username
          2. Comparer le mot de passe saisi avec le hash stocke via bcrypt.checkpw()
          3. Si ok, retourner l'id de l'utilisateur

        Args:
            username: nom d'utilisateur
            password: mot de passe a verifier

        Returns:
            (succes: bool, user_id: int ou None, message: str)
        """
        username = username.strip()
        if not username or not password:
            return False, None, "Veuillez remplir tous les champs"

        # Chercher l'utilisateur dans la base
        resultat = self.db.executer(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()

        if not resultat:
            return False, None, "Nom d'utilisateur ou mot de passe incorrect"

        # Comparer le mot de passe saisi avec le hash stocke
        # checkpw() re-hashe le mot de passe saisi avec le meme sel
        # et compare les deux hashes de maniere securisee (timing-safe)
        hash_stocke = resultat["password_hash"].encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), hash_stocke):
            logger.info(f"Connexion reussie: {username}")
            return True, resultat["id"], "Connexion reussie"
        else:
            return False, None, "Nom d'utilisateur ou mot de passe incorrect"

    def utilisateur_existe(self, username: str) -> bool:
        """Verifie si un nom d'utilisateur est deja pris."""
        resultat = self.db.executer(
            "SELECT id FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
        return resultat is not None

    def get_username(self, user_id: int) -> str | None:
        """Recupere le nom d'utilisateur a partir de son id."""
        resultat = self.db.executer(
            "SELECT username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return resultat["username"] if resultat else None
