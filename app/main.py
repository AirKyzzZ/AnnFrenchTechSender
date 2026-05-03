"""
main.py - Point d'entree de l'application FT Sender

Ce fichier lance l'application :
  1. Configure le systeme de logs (fichier + console)
  2. Initialise la base de donnees SQLite
  3. Applique le theme sombre CustomTkinter
  4. Cree et affiche la fenetre principale

L'application demarre toujours sur l'ecran de connexion.
Apres authentification, l'utilisateur accede au dashboard principal.
"""

import sys
import os
import logging
import customtkinter as ctk

# Ajouter le repertoire parent au path pour les imports
# Necessaire quand on lance le script directement (python app/main.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.database import Database
from app.ui.main_window import MainWindow


def setup_logging():
    """
    Configure le systeme de logging Python.

    Les logs sont envoyes vers deux destinations :
      - Un fichier (candidature_logs.log) pour garder un historique permanent
      - La console (stderr) pour le debug en temps reel

    Le format inclut : date/heure, nom du module, niveau, message.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("candidature_logs.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main():
    """Fonction principale : initialise et lance l'application."""
    setup_logging()

    # Initialiser la base de donnees SQLite
    # Les tables sont creees automatiquement si elles n'existent pas
    db = Database()

    # Theme CustomTkinter : mode sombre avec palette bleue
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Creer et lancer la fenetre principale
    # On passe l'instance de Database pour que toute l'app partage la meme connexion
    app = MainWindow(db)
    app.mainloop()

    # Fermer proprement la connexion a la base a la fin
    db.fermer()


if __name__ == "__main__":
    main()
