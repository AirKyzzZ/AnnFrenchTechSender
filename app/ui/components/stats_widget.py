import customtkinter as ctk
from app.ui.theme import COLORS, FONTS


class StatsWidget(ctk.CTkFrame):
    """Grille 2x3 affichant les statistiques en temps reel."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.labels: dict[str, ctk.CTkLabel] = {}

        items = [
            ("total", "Total", "0"),
            ("envoyes", "Envoyees", "0"),
            ("echecs", "Echecs", "0"),
            ("taux", "Taux de reussite", "0%"),
            ("traites", "Traitees", "0"),
            ("temps", "Temps ecoule", "--:--"),
        ]

        for i, (key, label, default) in enumerate(items):
            row, col = divmod(i, 3)
            card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Couleur de la valeur selon le type
            value_color = COLORS["text_primary"]
            if key == "envoyes":
                value_color = COLORS["success"]
            elif key == "echecs":
                value_color = COLORS["error"]
            elif key == "taux":
                value_color = COLORS["accent"]

            val_label = ctk.CTkLabel(
                card,
                text=default,
                font=FONTS["stat_value"],
                text_color=value_color,
            )
            val_label.pack(padx=15, pady=(12, 2))

            ctk.CTkLabel(
                card,
                text=label,
                font=FONTS["stat_label"],
                text_color=COLORS["text_muted"],
            ).pack(padx=15, pady=(0, 10))

            self.labels[key] = val_label

        for col in range(3):
            self.columnconfigure(col, weight=1)
        for row in range(2):
            self.rowconfigure(row, weight=0)

    def update_stats(self, stats: dict):
        self.labels["total"].configure(text=str(stats.get("total", 0)))
        self.labels["envoyes"].configure(text=str(stats.get("envoyes", 0)))
        self.labels["echecs"].configure(text=str(stats.get("echecs", 0)))
        taux = stats.get("taux_reussite", 0)
        self.labels["taux"].configure(text=f"{taux:.1f}%")
        self.labels["traites"].configure(text=str(stats.get("traites", 0)))

    def update_temps(self, temps: str):
        self.labels["temps"].configure(text=temps)

    def reset(self):
        for key, label in self.labels.items():
            if key == "temps":
                label.configure(text="--:--")
            elif key == "taux":
                label.configure(text="0%")
            else:
                label.configure(text="0")
