"""
navigation.py - Sidebar de navigation

Affiche les 5 onglets de l'application dans une barre laterale a gauche.
Le bouton actif est mis en surbrillance. En bas, affiche le nom de
l'utilisateur connecte et un bouton de deconnexion.
"""

import customtkinter as ctk
from app.ui.theme import COLORS, FONTS, SIZES


class Navigation(ctk.CTkFrame):
    """Sidebar de navigation avec 5 boutons + info utilisateur."""

    ITEMS = [
        ("Profil", "profile"),
        ("Envoi", "sending"),
        ("Liste Noire", "blacklist"),
        ("Journaux", "logs"),
        ("Parametres", "settings"),
    ]

    def __init__(self, parent, on_navigate, username: str = "", on_logout=None):
        """
        Args:
            parent: widget parent
            on_navigate: callback appele avec la cle du frame a afficher
            username: nom de l'utilisateur connecte (affiche en bas)
            on_logout: callback appele quand l'utilisateur clique sur Deconnexion
        """
        super().__init__(parent, width=SIZES["sidebar_width"], fg_color=COLORS["bg_sidebar"])
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.active = "profile"
        self.buttons: dict[str, ctk.CTkButton] = {}

        # Empecher le frame de se redimensionner selon son contenu
        self.grid_propagate(False)

        # Titre app
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(25, 5))

        ctk.CTkLabel(
            title_frame,
            text="FT Sender",
            font=FONTS["title"],
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="French Tech Bordeaux",
            font=FONTS["body_small"],
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        # Separateur
        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=15, pady=(15, 10))

        # Boutons de navigation
        for label, key in self.ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"  {label}",
                anchor="w",
                font=FONTS["nav"],
                fg_color="transparent",
                text_color=COLORS["text_secondary"],
                hover_color=COLORS["bg_hover"],
                height=40,
                corner_radius=6,
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.buttons[key] = btn

        self._highlight(self.active)

        # Section utilisateur en bas de la sidebar
        # pack_propagate(False) + pack(side="bottom") place cette section en bas
        if username:
            # Separateur avant la section utilisateur
            bottom_sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
            bottom_sep.pack(side="bottom", fill="x", padx=15, pady=(10, 0))

            user_frame = ctk.CTkFrame(self, fg_color="transparent")
            user_frame.pack(side="bottom", fill="x", padx=15, pady=(10, 15))

            # Nom de l'utilisateur connecte
            ctk.CTkLabel(
                user_frame,
                text=username,
                font=FONTS["body"],
                text_color=COLORS["text_primary"],
            ).pack(anchor="w")

            # Bouton de deconnexion
            if on_logout:
                ctk.CTkButton(
                    user_frame,
                    text="Deconnexion",
                    font=FONTS["body_small"],
                    height=30,
                    fg_color=COLORS["bg_input"],
                    hover_color=COLORS["error_bg"],
                    text_color=COLORS["text_muted"],
                    corner_radius=4,
                    command=on_logout,
                ).pack(fill="x", pady=(8, 0))

    def _navigate(self, key: str):
        """Change de frame et met a jour la surbrillance."""
        self.active = key
        self._highlight(key)
        self.on_navigate(key)

    def _highlight(self, active_key: str):
        """Met en surbrillance le bouton actif et reset les autres."""
        for key, btn in self.buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=COLORS["accent_dark"],
                    text_color=COLORS["text_primary"],
                    font=FONTS["nav_active"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                    font=FONTS["nav"],
                )
