import customtkinter as ctk
from app.ui.theme import COLORS, FONTS, SIZES


class Navigation(ctk.CTkFrame):
    """Sidebar de navigation avec 5 boutons."""

    ITEMS = [
        ("Profil", "profile"),
        ("Envoi", "sending"),
        ("Liste Noire", "blacklist"),
        ("Journaux", "logs"),
        ("Parametres", "settings"),
    ]

    def __init__(self, parent, on_navigate):
        super().__init__(parent, width=SIZES["sidebar_width"], fg_color=COLORS["bg_sidebar"])
        self.on_navigate = on_navigate
        self.active = "profile"
        self.buttons: dict[str, ctk.CTkButton] = {}

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

        # Boutons navigation
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

    def _navigate(self, key: str):
        self.active = key
        self._highlight(key)
        self.on_navigate(key)

    def _highlight(self, active_key: str):
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
