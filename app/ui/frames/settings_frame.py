import customtkinter as ctk
from app.ui.theme import COLORS, FONTS, SIZES
from app.data.models import Settings
from app.data.config_manager import ConfigManager


class SettingsFrame(ctk.CTkFrame):
    """Parametres de l'application: delays, timeout, headless, paths."""

    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.config_manager = config_manager
        self.widgets: dict = {}

        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        # Titre
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SIZES["padding"], pady=(SIZES["padding"], 10))

        ctk.CTkLabel(header, text="Parametres", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).pack(side="left")

        ctk.CTkButton(
            header, text="Enregistrer", font=FONTS["button"], width=120, height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=6, command=self._save_settings,
        ).pack(side="right")

        # Contenu scrollable
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SIZES["padding"], pady=(0, SIZES["padding"]))

        # -- Section Timing --
        self._section_title(content, "Timing")

        self.widgets["delay_min"] = self._slider_field(
            content, "Delai minimum entre envois (secondes)", 0.5, 10.0, 2.0
        )
        self.widgets["delay_max"] = self._slider_field(
            content, "Delai maximum entre envois (secondes)", 1.0, 20.0, 5.0
        )
        self.widgets["timeout_page"] = self._slider_field(
            content, "Timeout chargement page (secondes)", 10, 120, 30, step=5
        )
        self.widgets["timeout_bouton"] = self._slider_field(
            content, "Timeout attente bouton anti-bot (secondes)", 60, 600, 240, step=30
        )
        self.widgets["max_tentatives"] = self._slider_field(
            content, "Tentatives maximum par entreprise", 1, 10, 5, step=1
        )

        # -- Section Chrome --
        self._section_title(content, "Chrome")

        self.widgets["headless"] = self._switch_field(
            content, "Mode arriere-plan (headless)", True
        )
        self.widgets["rotation_active"] = self._switch_field(
            content, "Rotation de session automatique", False
        )
        self.widgets["duree_session_minutes"] = self._slider_field(
            content, "Duree de session avant rotation (minutes)", 5, 60, 15, step=5
        )
        self.widgets["pause_entre_sessions_minutes"] = self._slider_field(
            content, "Pause entre sessions (minutes)", 1, 15, 4, step=1
        )

        # -- Section Fichiers --
        self._section_title(content, "Fichiers")

        self.widgets["csv_path"] = self._entry_field(content, "Fichier CSV des URLs", "urls_entreprises.csv")
        self.widgets["blacklist_path"] = self._entry_field(content, "Fichier liste noire", "blacklist.txt")
        self.widgets["log_path"] = self._entry_field(content, "Fichier de logs", "candidature_logs.log")

        # Status
        self.status_label = ctk.CTkLabel(
            content, text="", font=FONTS["body_small"],
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack(anchor="w", pady=(10, 0))

    def _section_title(self, parent, text: str):
        ctk.CTkLabel(
            parent, text=text, font=FONTS["subtitle"],
            text_color=COLORS["accent"],
        ).pack(anchor="w", pady=(20, 5))

        sep = ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", pady=(0, 10))

    def _slider_field(self, parent, label: str, min_val: float, max_val: float,
                      default: float, step: float = 0.5) -> dict:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        label_widget = ctk.CTkLabel(frame, text=label, font=FONTS["body"],
                                    text_color=COLORS["text_secondary"])
        label_widget.pack(anchor="w")

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")

        value_label = ctk.CTkLabel(row, text=str(default), font=FONTS["body"],
                                   text_color=COLORS["text_primary"], width=50)
        value_label.pack(side="right", padx=(10, 0))

        slider = ctk.CTkSlider(
            row, from_=min_val, to=max_val, number_of_steps=int((max_val - min_val) / step),
            fg_color=COLORS["bg_input"], progress_color=COLORS["accent"],
            button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            command=lambda v, lbl=value_label, s=step: lbl.configure(
                text=str(int(v)) if s >= 1 else f"{v:.1f}"
            ),
        )
        slider.set(default)
        slider.pack(side="left", fill="x", expand=True)

        return {"slider": slider, "label": value_label, "step": step}

    def _switch_field(self, parent, label: str, default: bool) -> dict:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        var = ctk.BooleanVar(value=default)

        ctk.CTkLabel(frame, text=label, font=FONTS["body"],
                     text_color=COLORS["text_secondary"]).pack(side="left")

        switch = ctk.CTkSwitch(
            frame, text="", variable=var,
            fg_color=COLORS["bg_input"], progress_color=COLORS["accent"],
            button_color=COLORS["text_primary"], button_hover_color=COLORS["accent"],
        )
        switch.pack(side="right")

        return {"var": var}

    def _entry_field(self, parent, label: str, default: str) -> dict:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(frame, text=label, font=FONTS["body"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 4))

        entry = ctk.CTkEntry(
            frame, font=FONTS["body"], fg_color=COLORS["bg_input"],
            border_color=COLORS["border"], text_color=COLORS["text_primary"],
            corner_radius=6, height=SIZES["input_height"],
        )
        entry.insert(0, default)
        entry.pack(fill="x")

        return {"entry": entry}

    def _load_settings(self):
        settings = self.config_manager.load()
        data = settings.to_dict()

        for key, widget_info in self.widgets.items():
            value = data.get(key)
            if value is None:
                continue

            if "slider" in widget_info:
                widget_info["slider"].set(value)
                step = widget_info["step"]
                widget_info["label"].configure(
                    text=str(int(value)) if step >= 1 else f"{value:.1f}"
                )
            elif "var" in widget_info:
                widget_info["var"].set(value)
            elif "entry" in widget_info:
                widget_info["entry"].delete(0, "end")
                widget_info["entry"].insert(0, str(value))

    def _save_settings(self):
        data = {}
        for key, widget_info in self.widgets.items():
            if "slider" in widget_info:
                val = widget_info["slider"].get()
                step = widget_info["step"]
                data[key] = int(val) if step >= 1 else round(val, 1)
            elif "var" in widget_info:
                data[key] = widget_info["var"].get()
            elif "entry" in widget_info:
                data[key] = widget_info["entry"].get()

        settings = Settings.from_dict(data)
        self.config_manager.save(settings)
        self.status_label.configure(text="Parametres enregistres", text_color=COLORS["success"])

    def get_settings(self) -> Settings:
        self._save_settings()
        return self.config_manager.load()
