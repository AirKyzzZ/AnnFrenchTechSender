import customtkinter as ctk
from app.ui.theme import COLORS, FONTS, SIZES
from app.data.models import UserProfile
from app.data.profile_manager import ProfileManager


class ProfileFrame(ctk.CTkFrame):
    """Formulaire de profil utilisateur (nom, prenom, email, tel, objet, message)."""

    def __init__(self, parent, profile_manager: ProfileManager):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.profile_manager = profile_manager
        self.entries: dict[str, ctk.CTkEntry | ctk.CTkTextbox] = {}

        self._build_ui()
        self._load_profile()

    def _build_ui(self):
        # Titre
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SIZES["padding"], pady=(SIZES["padding"], 10))

        ctk.CTkLabel(header, text="Profil Candidat", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).pack(side="left")

        # Boutons en haut a droite
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Enregistrer", font=FONTS["button"], width=120, height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=6, command=self._save_profile,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Recharger", font=FONTS["button"], width=100, height=36,
            fg_color=COLORS["bg_card"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_secondary"], corner_radius=6,
            command=self._load_profile,
        ).pack(side="left", padx=5)

        # Formulaire dans un cadre scrollable
        form_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=SIZES["padding"], pady=(0, SIZES["padding"]))

        fields = [
            ("nom", "Nom", "entry"),
            ("prenom", "Prenom", "entry"),
            ("email", "Email", "entry"),
            ("telephone", "Telephone", "entry"),
            ("objet", "Objet du message", "entry"),
            ("message", "Message", "textbox"),
        ]

        for key, label, field_type in fields:
            # Label
            ctk.CTkLabel(
                form_container, text=label, font=FONTS["body"],
                text_color=COLORS["text_secondary"],
            ).pack(anchor="w", pady=(12, 4))

            if field_type == "entry":
                entry = ctk.CTkEntry(
                    form_container,
                    height=SIZES["input_height"],
                    font=FONTS["body"],
                    fg_color=COLORS["bg_input"],
                    border_color=COLORS["border"],
                    text_color=COLORS["text_primary"],
                    corner_radius=6,
                )
                entry.pack(fill="x")
                self.entries[key] = entry
            else:
                textbox = ctk.CTkTextbox(
                    form_container,
                    height=200,
                    font=FONTS["body"],
                    fg_color=COLORS["bg_input"],
                    border_color=COLORS["border"],
                    text_color=COLORS["text_primary"],
                    corner_radius=6,
                    wrap="word",
                )
                textbox.pack(fill="x")
                self.entries[key] = textbox

        # Status
        self.status_label = ctk.CTkLabel(
            form_container, text="", font=FONTS["body_small"],
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack(anchor="w", pady=(10, 0))

    def _load_profile(self):
        profile = self.profile_manager.load()
        data = profile.to_dict()

        for key, widget in self.entries.items():
            value = data.get(key, "")
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
                widget.insert(0, value)
            else:
                widget.delete("1.0", "end")
                widget.insert("1.0", value)

        self.status_label.configure(text="Profil charge", text_color=COLORS["text_muted"])

    def _save_profile(self):
        profile = self.get_profile()
        self.profile_manager.save(profile)
        self.status_label.configure(text="Profil enregistre avec succes", text_color=COLORS["success"])

    def get_profile(self) -> UserProfile:
        data = {}
        for key, widget in self.entries.items():
            if isinstance(widget, ctk.CTkEntry):
                data[key] = widget.get()
            else:
                data[key] = widget.get("1.0", "end-1c")
        return UserProfile.from_dict(data)
