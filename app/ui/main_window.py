"""
main_window.py - Fenetre principale de l'application

Cette fenetre gere deux etats :
  1. Ecran de connexion (avant authentification)
  2. Dashboard principal (apres authentification, avec sidebar + contenu)

Le passage de l'un a l'autre se fait via la methode _on_login_success()
qui est appelee par le LoginFrame quand l'utilisateur se connecte.

Architecture : la fenetre principale cree tous les managers (profil, config,
blacklist, historique) et les passe aux frames enfants. C'est le "chef
d'orchestre" de l'application.
"""

import customtkinter as ctk
from app.ui.theme import COLORS, SIZES
from app.ui.components.navigation import Navigation
from app.ui.frames.login_frame import LoginFrame
from app.ui.frames.profile_frame import ProfileFrame
from app.ui.frames.sending_frame import SendingFrame
from app.ui.frames.blacklist_frame import BlacklistFrame
from app.ui.frames.logs_frame import LogsFrame
from app.ui.frames.settings_frame import SettingsFrame
from app.data.database import Database
from app.data.auth_manager import AuthManager
from app.data.profile_manager import ProfileManager
from app.data.blacklist_manager import BlacklistManager
from app.data.config_manager import ConfigManager
from app.data.history_manager import HistoryManager


class MainWindow(ctk.CTk):
    """
    Fenetre principale avec deux modes :
      - Mode login : affiche le formulaire de connexion
      - Mode app   : affiche la sidebar + les frames de l'application
    """

    def __init__(self, db: Database):
        super().__init__()

        self.db = db
        self.user_id: int | None = None
        self.username: str = ""

        self.title("FT Sender - French Tech Bordeaux")
        self.geometry(f"{SIZES['window_width']}x{SIZES['window_height']}")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_dark"])

        # Layout principal : une seule colonne extensible
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Creer le gestionnaire d'authentification
        self.auth_manager = AuthManager(db)

        # Afficher l'ecran de connexion au demarrage
        self._show_login()

    def _show_login(self):
        """Affiche l'ecran de connexion."""
        # Nettoyer la fenetre (utile apres une deconnexion)
        for widget in self.winfo_children():
            widget.destroy()

        # Re-configurer le layout pour le login (1 colonne, centree)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Creer et afficher le frame de connexion
        self.login_frame = LoginFrame(self, self.auth_manager, self._on_login_success)
        self.login_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def _on_login_success(self, user_id: int, username: str):
        """
        Callback appele par LoginFrame apres une connexion reussie.

        Cree tous les managers avec le user_id, puis affiche le dashboard.

        Args:
            user_id: id de l'utilisateur connecte (depuis la table users)
            username: nom d'utilisateur (pour l'affichage dans la sidebar)
        """
        self.user_id = user_id
        self.username = username

        # Creer les managers lies a l'utilisateur connecte
        self.config_manager = ConfigManager()
        settings = self.config_manager.load()
        self.profile_manager = ProfileManager(self.db, user_id)
        self.blacklist_manager = BlacklistManager(settings.blacklist_path)
        self.history_manager = HistoryManager(self.db, user_id)

        # Passer au dashboard
        self._show_dashboard()

    def _show_dashboard(self):
        """Construit et affiche le dashboard principal (sidebar + contenu)."""
        # Nettoyer la fenetre
        for widget in self.winfo_children():
            widget.destroy()

        # Layout : colonne 0 = sidebar, colonne 1 = contenu (extensible)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar de navigation
        self.navigation = Navigation(
            self,
            on_navigate=self._show_frame,
            username=self.username,
            on_logout=self._on_logout,
        )
        self.navigation.grid(row=0, column=0, sticky="ns")

        # Zone de contenu
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Creer les frames de chaque section
        self.frames: dict[str, ctk.CTkFrame] = {}
        self.frames["profile"] = ProfileFrame(self.content, self.profile_manager)
        self.frames["sending"] = SendingFrame(
            self.content, self.profile_manager, self.config_manager, self.history_manager
        )
        self.frames["blacklist"] = BlacklistFrame(self.content, self.blacklist_manager)
        self.frames["logs"] = LogsFrame(self.content)
        self.frames["settings"] = SettingsFrame(self.content, self.config_manager)

        # Afficher le profil par defaut
        self._show_frame("profile")

    def _show_frame(self, key: str):
        """
        Affiche un frame et cache les autres.

        C'est le systeme de navigation de l'application : chaque bouton
        de la sidebar appelle cette methode avec la cle du frame a afficher.
        """
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[key].grid(row=0, column=0, sticky="nsew")

    def _on_logout(self):
        """
        Deconnecte l'utilisateur et revient a l'ecran de connexion.

        Remet a zero l'etat de la fenetre (user_id, frames, etc.).
        """
        self.user_id = None
        self.username = ""
        self.frames = {}
        self._show_login()
