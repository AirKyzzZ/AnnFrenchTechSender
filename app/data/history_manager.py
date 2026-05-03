"""
history_manager.py - Gestionnaire de l'historique des envois

Ce module enregistre chaque envoi de candidature (succes ou echec) dans SQLite.
Il permet de :
  - Ne pas renvoyer a une entreprise deja contactee avec succes
  - Consulter l'historique complet des envois
  - Calculer des statistiques (nombre d'envois, taux de reussite, etc.)

C'est la solution au probleme "le programme refait les memes entreprises
quand on le relance" : avant chaque envoi, on verifie si l'URL est deja
dans l'historique avec le statut 'succes'.
"""

import logging
from datetime import datetime
from app.data.database import Database

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Gere l'historique des envois de candidatures dans SQLite.

    Chaque envoi est enregistre avec : URL, nom de l'organisation,
    statut (succes/echec), nombre de tentatives, et date.
    """

    def __init__(self, db: Database, user_id: int):
        """
        Args:
            db: instance de Database pour les requetes SQL
            user_id: id de l'utilisateur connecte (filtre les donnees par user)
        """
        self.db = db
        self.user_id = user_id

    def enregistrer_envoi(self, url: str, statut: str, tentatives: int = 1):
        """
        Enregistre un envoi dans l'historique.

        Args:
            url: URL de l'organisation contactee
            statut: 'succes' ou 'echec'
            tentatives: nombre de tentatives effectuees
        """
        # Extraire le nom de l'organisation depuis l'URL
        # Ex: "https://.../organisations/mon-entreprise" → "mon-entreprise"
        organisation = url.split("/organisations/")[-1] if "/organisations/" in url else url

        self.db.executer(
            """INSERT INTO historique (user_id, url, organisation, statut, tentatives, date_envoi)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (self.user_id, url, organisation, statut, tentatives,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        self.db.commit()
        logger.info(f"Historique enregistre: {organisation} -> {statut}")

    def deja_envoye(self, url: str) -> bool:
        """
        Verifie si une candidature a DEJA ete envoyee avec succes a cette URL.

        On ne filtre que les envois reussis : si un envoi a echoue,
        on peut retenter. Seuls les succes sont consideres comme "deja fait".

        Args:
            url: URL de l'organisation a verifier

        Returns:
            True si l'URL a deja ete contactee avec succes
        """
        resultat = self.db.executer(
            "SELECT id FROM historique WHERE user_id = ? AND url = ? AND statut = 'succes'",
            (self.user_id, url),
        ).fetchone()
        return resultat is not None

    def get_urls_envoyees(self) -> set[str]:
        """
        Recupere l'ensemble des URLs deja envoyees avec succes.

        Retourne un set pour des recherches rapides en O(1)
        (plus performant qu'une liste quand on fait beaucoup de "url in set").

        Returns:
            Set des URLs deja contactees avec succes
        """
        resultats = self.db.executer(
            "SELECT url FROM historique WHERE user_id = ? AND statut = 'succes'",
            (self.user_id,),
        ).fetchall()
        return {row["url"] for row in resultats}

    def get_historique(self, limite: int = 100) -> list[dict]:
        """
        Recupere les derniers envois de l'historique.

        Args:
            limite: nombre maximum d'entrees a retourner (defaut: 100)

        Returns:
            Liste de dicts avec les infos de chaque envoi
        """
        resultats = self.db.executer(
            """SELECT url, organisation, statut, tentatives, date_envoi
               FROM historique
               WHERE user_id = ?
               ORDER BY date_envoi DESC
               LIMIT ?""",
            (self.user_id, limite),
        ).fetchall()

        return [
            {
                "url": row["url"],
                "organisation": row["organisation"],
                "statut": row["statut"],
                "tentatives": row["tentatives"],
                "date_envoi": row["date_envoi"],
            }
            for row in resultats
        ]

    def compter_envois(self) -> dict:
        """
        Calcule les statistiques globales d'envoi pour cet utilisateur.

        Utilise COUNT avec CASE WHEN pour compter succes et echecs
        en une seule requete SQL (plus efficace que 2 requetes separees).

        Returns:
            Dict avec total, succes, echecs
        """
        resultat = self.db.executer(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN statut = 'succes' THEN 1 ELSE 0 END) as succes,
                SUM(CASE WHEN statut = 'echec' THEN 1 ELSE 0 END) as echecs
               FROM historique
               WHERE user_id = ?""",
            (self.user_id,),
        ).fetchone()

        return {
            "total": resultat["total"] or 0,
            "succes": resultat["succes"] or 0,
            "echecs": resultat["echecs"] or 0,
        }
