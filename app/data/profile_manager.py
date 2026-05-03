"""
profile_manager.py - Gestionnaire des profils de candidature

Ce module gere la sauvegarde et le chargement des profils utilisateur.
Les profils sont stockes dans SQLite (table profiles), lies a l'utilisateur connecte.

Avant, les profils etaient en fichiers JSON. On a migre vers SQLite pour :
  → Lier le profil a un utilisateur (relation user_id → profiles)
  → Beneficier des transactions SQL (pas de corruption de fichier)
  → Centraliser toutes les donnees relationnelles dans une seule base

La blacklist et la config restent en JSON/TXT car ce sont des donnees
simples sans relations → approche NoSQL complementaire.
"""

import logging
from app.data.models import UserProfile
from app.data.database import Database

logger = logging.getLogger(__name__)


class ProfileManager:
    """
    Gere le profil de candidature d'un utilisateur dans SQLite.

    Chaque utilisateur a un seul profil (contrainte UNIQUE sur user_id).
    Le profil contient : nom, prenom, email, telephone, objet, message.
    """

    def __init__(self, db: Database, user_id: int):
        """
        Args:
            db: instance de Database pour les requetes SQL
            user_id: id de l'utilisateur connecte
        """
        self.db = db
        self.user_id = user_id

    def save(self, profile: UserProfile) -> None:
        """
        Sauvegarde le profil en base.

        Utilise INSERT OR REPLACE : si le profil existe deja pour cet utilisateur,
        il est remplace. Sinon, il est cree. C'est un "upsert" simplifie.
        (upsert = UPDATE si existe, INSERT sinon)
        """
        # Verifier si un profil existe deja pour cet utilisateur
        existant = self.db.executer(
            "SELECT id FROM profiles WHERE user_id = ?", (self.user_id,)
        ).fetchone()

        if existant:
            # Mettre a jour le profil existant
            self.db.executer(
                """UPDATE profiles
                   SET nom=?, prenom=?, email=?, telephone=?, objet=?, message=?
                   WHERE user_id=?""",
                (profile.nom, profile.prenom, profile.email,
                 profile.telephone, profile.objet, profile.message, self.user_id),
            )
        else:
            # Creer un nouveau profil
            self.db.executer(
                """INSERT INTO profiles (user_id, nom, prenom, email, telephone, objet, message)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (self.user_id, profile.nom, profile.prenom, profile.email,
                 profile.telephone, profile.objet, profile.message),
            )

        self.db.commit()
        logger.info(f"Profil sauvegarde pour l'utilisateur {self.user_id}")

    def load(self) -> UserProfile:
        """
        Charge le profil de l'utilisateur depuis la base.

        Returns:
            UserProfile rempli si un profil existe, sinon un profil vide.
        """
        resultat = self.db.executer(
            "SELECT nom, prenom, email, telephone, objet, message FROM profiles WHERE user_id = ?",
            (self.user_id,),
        ).fetchone()

        if not resultat:
            # Aucun profil enregistre, retourner un profil vide
            return UserProfile()

        return UserProfile(
            nom=resultat["nom"],
            prenom=resultat["prenom"],
            email=resultat["email"],
            telephone=resultat["telephone"],
            objet=resultat["objet"],
            message=resultat["message"],
        )

    def exists(self) -> bool:
        """Verifie si un profil existe pour cet utilisateur."""
        resultat = self.db.executer(
            "SELECT id FROM profiles WHERE user_id = ?", (self.user_id,)
        ).fetchone()
        return resultat is not None

    def delete(self) -> bool:
        """Supprime le profil de l'utilisateur."""
        self.db.executer("DELETE FROM profiles WHERE user_id = ?", (self.user_id,))
        self.db.commit()
        return True
