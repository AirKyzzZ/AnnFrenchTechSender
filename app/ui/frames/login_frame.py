"""
login_frame.py - Ecran de connexion / inscription

Cet ecran s'affiche au lancement de l'application. L'utilisateur doit
s'authentifier avant d'acceder aux fonctionnalites de l'application.
Deux modes : connexion (compte existant) ou inscription (nouveau compte).

L'authentification est locale (pas de serveur distant) : les identifiants
sont stockes dans la base SQLite avec un hash bcrypt pour le mot de passe.
"""

import customtkinter as ctk
from app.ui.theme import COLORS, FONTS, SIZES
from app.data.auth_manager import AuthManager


class LoginFrame(ctk.CTkFrame):
    """
    Formulaire de connexion / inscription.

    L'utilisateur peut basculer entre les modes "Connexion" et "Inscription"
    via un lien en bas du formulaire. Le callback on_login_success est appele
    quand l'authentification reussit, avec l'user_id en parametre.
    """

    def __init__(self, parent, auth_manager: AuthManager, on_login_success):
        """
        Args:
            parent: widget parent (la fenetre principale)
            auth_manager: gestionnaire d'authentification (bcrypt + SQLite)
            on_login_success: callback appele avec (user_id, username) apres connexion
        """
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.auth_manager = auth_manager
        self.on_login_success = on_login_success

        # Mode actuel : "login" ou "register"
        self.mode = "login"

        self._build_ui()

    def _build_ui(self):
        """Construit l'interface du formulaire de connexion."""
        # Centrer le formulaire verticalement et horizontalement
        # en utilisant un frame intermediaire avec expand
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Conteneur central (largeur fixe pour un aspect propre)
        center = ctk.CTkFrame(self, fg_color="transparent", width=400)
        center.grid(row=0, column=0)

        # Titre de l'application
        ctk.CTkLabel(
            center, text="FT Sender", font=("Segoe UI", 28, "bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            center, text="French Tech Bordeaux", font=FONTS["body"],
            text_color=COLORS["text_muted"],
        ).pack(pady=(0, 30))

        # Cadre du formulaire avec fond
        form_card = ctk.CTkFrame(center, fg_color=COLORS["bg_card"], corner_radius=12)
        form_card.pack(fill="x", padx=20)

        # Titre du formulaire (change selon le mode)
        self.form_title = ctk.CTkLabel(
            form_card, text="Connexion", font=FONTS["subtitle"],
            text_color=COLORS["text_primary"],
        )
        self.form_title.pack(padx=30, pady=(25, 20))

        # Champ nom d'utilisateur
        ctk.CTkLabel(
            form_card, text="Nom d'utilisateur", font=FONTS["body_small"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=30)

        self.username_entry = ctk.CTkEntry(
            form_card, height=SIZES["input_height"], font=FONTS["body"],
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"], corner_radius=6,
            placeholder_text="Entrez votre nom d'utilisateur",
        )
        self.username_entry.pack(fill="x", padx=30, pady=(5, 15))

        # Champ mot de passe
        ctk.CTkLabel(
            form_card, text="Mot de passe", font=FONTS["body_small"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=30)

        self.password_entry = ctk.CTkEntry(
            form_card, height=SIZES["input_height"], font=FONTS["body"],
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"], corner_radius=6,
            placeholder_text="Entrez votre mot de passe",
            show="*",  # Masquer les caracteres avec des etoiles
        )
        self.password_entry.pack(fill="x", padx=30, pady=(5, 10))

        # Champ confirmation (visible uniquement en mode inscription)
        self.confirm_label = ctk.CTkLabel(
            form_card, text="Confirmer le mot de passe", font=FONTS["body_small"],
            text_color=COLORS["text_secondary"],
        )

        self.confirm_entry = ctk.CTkEntry(
            form_card, height=SIZES["input_height"], font=FONTS["body"],
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"], corner_radius=6,
            placeholder_text="Confirmez votre mot de passe",
            show="*",
        )

        # Message d'erreur / succes
        self.message_label = ctk.CTkLabel(
            form_card, text="", font=FONTS["body_small"],
            text_color=COLORS["error"],
        )
        self.message_label.pack(padx=30, pady=(5, 5))

        # Bouton principal (Connexion ou Inscription)
        self.action_btn = ctk.CTkButton(
            form_card, text="Se connecter", font=FONTS["button"],
            height=40, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=6, command=self._on_action,
        )
        self.action_btn.pack(fill="x", padx=30, pady=(5, 15))

        # Lien pour basculer entre connexion et inscription
        self.toggle_btn = ctk.CTkButton(
            form_card, text="Pas encore de compte ? S'inscrire",
            font=FONTS["body_small"], fg_color="transparent",
            text_color=COLORS["accent"], hover_color=COLORS["bg_hover"],
            command=self._toggle_mode,
        )
        self.toggle_btn.pack(pady=(0, 20))

        # Permettre l'envoi avec la touche Entree
        self.username_entry.bind("<Return>", lambda e: self._on_action())
        self.password_entry.bind("<Return>", lambda e: self._on_action())
        self.confirm_entry.bind("<Return>", lambda e: self._on_action())

    def _toggle_mode(self):
        """Bascule entre le mode connexion et inscription."""
        if self.mode == "login":
            self.mode = "register"
            self.form_title.configure(text="Inscription")
            self.action_btn.configure(text="S'inscrire")
            self.toggle_btn.configure(text="Deja un compte ? Se connecter")
            # Afficher le champ de confirmation
            self.confirm_label.pack(anchor="w", padx=30, before=self.message_label)
            self.confirm_entry.pack(fill="x", padx=30, pady=(5, 10), before=self.message_label)
        else:
            self.mode = "login"
            self.form_title.configure(text="Connexion")
            self.action_btn.configure(text="Se connecter")
            self.toggle_btn.configure(text="Pas encore de compte ? S'inscrire")
            # Cacher le champ de confirmation
            self.confirm_label.pack_forget()
            self.confirm_entry.pack_forget()

        # Effacer les messages et champs
        self.message_label.configure(text="")
        self.password_entry.delete(0, "end")
        self.confirm_entry.delete(0, "end")

    def _on_action(self):
        """Gere le clic sur le bouton principal (connexion ou inscription)."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if self.mode == "register":
            self._inscrire(username, password)
        else:
            self._connecter(username, password)

    def _inscrire(self, username: str, password: str):
        """Tente d'inscrire un nouvel utilisateur."""
        confirm = self.confirm_entry.get()

        # Verifier que les mots de passe correspondent
        if password != confirm:
            self.message_label.configure(
                text="Les mots de passe ne correspondent pas",
                text_color=COLORS["error"],
            )
            return

        succes, message = self.auth_manager.inscrire(username, password)

        if succes:
            self.message_label.configure(text=message, text_color=COLORS["success"])
            # Basculer automatiquement vers le mode connexion
            self._toggle_mode()
            # Pre-remplir le nom d'utilisateur
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, username)
        else:
            self.message_label.configure(text=message, text_color=COLORS["error"])

    def _connecter(self, username: str, password: str):
        """Tente de connecter l'utilisateur."""
        succes, user_id, message = self.auth_manager.connecter(username, password)

        if succes:
            # Appeler le callback avec l'id et le nom de l'utilisateur
            self.on_login_success(user_id, username)
        else:
            self.message_label.configure(text=message, text_color=COLORS["error"])
