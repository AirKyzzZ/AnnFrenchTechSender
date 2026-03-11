import customtkinter as ctk
from app.ui.theme import COLORS, FONTS


LEVEL_COLORS = {
    "info": COLORS["text_secondary"],
    "success": COLORS["success"],
    "warning": COLORS["warning"],
    "error": COLORS["error"],
}

LEVEL_PREFIX = {
    "info": "[INFO]",
    "success": "[OK]",
    "warning": "[WARN]",
    "error": "[ERREUR]",
}


class LogViewer(ctk.CTkFrame):
    """Textbox coloree par niveau de log avec filtre et auto-scroll."""

    def __init__(self, parent, height: int = 300):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8)

        self._filter_level = "all"
        self._entries: list[dict] = []

        # Barre de filtres
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(filter_bar, text="Filtre:", font=FONTS["body_small"],
                     text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 5))

        for level_name, level_key in [("Tout", "all"), ("Info", "info"), ("Succes", "success"),
                                       ("Alertes", "warning"), ("Erreurs", "error")]:
            btn = ctk.CTkButton(
                filter_bar,
                text=level_name,
                width=60,
                height=26,
                font=FONTS["body_small"],
                fg_color=COLORS["bg_input"],
                hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_secondary"],
                corner_radius=4,
                command=lambda k=level_key: self._set_filter(k),
            )
            btn.pack(side="left", padx=2)

        # Bouton effacer
        ctk.CTkButton(
            filter_bar,
            text="Effacer",
            width=60,
            height=26,
            font=FONTS["body_small"],
            fg_color=COLORS["error_bg"],
            hover_color=COLORS["error"],
            text_color=COLORS["error"],
            corner_radius=4,
            command=self.clear,
        ).pack(side="right", padx=2)

        # Zone de texte
        self.textbox = ctk.CTkTextbox(
            self,
            height=height,
            font=FONTS["mono_small"],
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text_secondary"],
            corner_radius=6,
            state="disabled",
            wrap="word",
        )
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def add_log(self, level: str, message: str, timestamp: str = ""):
        entry = {"level": level, "message": message, "timestamp": timestamp}
        self._entries.append(entry)

        if self._filter_level != "all" and level != self._filter_level:
            return

        self._write_entry(entry)

    def _write_entry(self, entry: dict):
        level = entry["level"]
        prefix = LEVEL_PREFIX.get(level, "[INFO]")
        color = LEVEL_COLORS.get(level, COLORS["text_secondary"])
        ts = f"[{entry['timestamp']}] " if entry.get("timestamp") else ""

        line = f"{ts}{prefix} {entry['message']}\n"

        self.textbox.configure(state="normal")
        self.textbox.insert("end", line)
        self.textbox.configure(state="disabled")
        self.textbox.see("end")

    def _set_filter(self, level: str):
        self._filter_level = level
        self._redraw()

    def _redraw(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

        for entry in self._entries:
            if self._filter_level == "all" or entry["level"] == self._filter_level:
                self._write_entry(entry)

    def clear(self):
        self._entries.clear()
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
