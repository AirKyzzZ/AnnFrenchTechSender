import customtkinter as ctk
from app.ui.theme import COLORS, FONTS, SIZES
from app.data.blacklist_manager import BlacklistManager


class BlacklistFrame(ctk.CTkFrame):
    """Gestion de la liste noire: liste scrollable, recherche, ajout, suppression."""

    def __init__(self, parent, blacklist_manager: BlacklistManager):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.blacklist_manager = blacklist_manager

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # Titre
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SIZES["padding"], pady=(SIZES["padding"], 10))

        ctk.CTkLabel(header, text="Liste Noire", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).pack(side="left")

        self.count_label = ctk.CTkLabel(
            header, text="0 organisations", font=FONTS["body_small"],
            text_color=COLORS["text_muted"],
        )
        self.count_label.pack(side="left", padx=(15, 0))

        # Barre ajout
        add_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8)
        add_frame.pack(fill="x", padx=SIZES["padding"], pady=(0, 10))

        ctk.CTkLabel(add_frame, text="Ajouter une URL:", font=FONTS["body_small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(10, 5))

        input_row = ctk.CTkFrame(add_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=15, pady=(0, 10))

        self.add_entry = ctk.CTkEntry(
            input_row, placeholder_text="https://annuaire.frenchtechbordeaux.com/organisations/...",
            font=FONTS["body"], fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"], corner_radius=6, height=SIZES["input_height"],
        )
        self.add_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            input_row, text="Ajouter", font=FONTS["button"], width=100, height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=6, command=self._add_url,
        ).pack(side="right")

        # Barre recherche
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=SIZES["padding"], pady=(0, 5))

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Rechercher...",
            font=FONTS["body"], fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"], corner_radius=6, height=SIZES["input_height"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_list())

        # Liste
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=8,
        )
        self.list_frame.pack(fill="both", expand=True, padx=SIZES["padding"], pady=(5, SIZES["padding"]))

        # Status
        self.status_label = ctk.CTkLabel(
            self, text="", font=FONTS["body_small"],
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack(anchor="w", padx=SIZES["padding"], pady=(0, 10))

    def _refresh_list(self, filter_text: str = ""):
        # Vider la liste
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        urls = self.blacklist_manager.load()
        self.count_label.configure(text=f"{len(urls)} organisations")

        if filter_text:
            urls = [u for u in urls if filter_text.lower() in u.lower()]

        if not urls:
            ctk.CTkLabel(
                self.list_frame, text="Aucune organisation dans la liste noire",
                font=FONTS["body"], text_color=COLORS["text_muted"],
            ).pack(pady=20)
            return

        for url in urls:
            row = ctk.CTkFrame(self.list_frame, fg_color=COLORS["bg_input"], corner_radius=6, height=40)
            row.pack(fill="x", pady=2, padx=5)
            row.pack_propagate(False)

            # Nom de l'organisation
            name = url.split("/organisations/")[-1] if "/organisations/" in url else url
            ctk.CTkLabel(
                row, text=name, font=FONTS["body"], text_color=COLORS["text_primary"],
            ).pack(side="left", padx=10)

            # Bouton supprimer
            ctk.CTkButton(
                row, text="X", width=30, height=28, font=FONTS["body_small"],
                fg_color=COLORS["error_bg"], hover_color=COLORS["error"],
                text_color=COLORS["error"], corner_radius=4,
                command=lambda u=url: self._remove_url(u),
            ).pack(side="right", padx=10, pady=5)

    def _filter_list(self):
        self._refresh_list(self.search_entry.get())

    def _add_url(self):
        url = self.add_entry.get().strip()
        if not url:
            return
        if self.blacklist_manager.add(url):
            self.add_entry.delete(0, "end")
            self.status_label.configure(text=f"URL ajoutee: {url}", text_color=COLORS["success"])
        else:
            self.status_label.configure(text="URL deja dans la liste", text_color=COLORS["warning"])
        self._refresh_list()

    def _remove_url(self, url: str):
        self.blacklist_manager.remove(url)
        name = url.split("/organisations/")[-1] if "/organisations/" in url else url
        self.status_label.configure(text=f"URL retiree: {name}", text_color=COLORS["text_muted"])
        self._refresh_list(self.search_entry.get())
