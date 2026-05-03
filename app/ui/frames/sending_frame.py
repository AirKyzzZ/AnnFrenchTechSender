"""
sending_frame.py - Dashboard d'envoi des candidatures

Cet ecran est le coeur de l'application. Il affiche :
  - Les boutons de controle (demarrer, pause, arreter)
  - Les statistiques en temps reel (envoyes, echecs, taux)
  - La barre de progression
  - L'entreprise en cours de traitement
  - Les logs d'evenements recents

La communication avec le moteur d'envoi (SenderEngine) se fait via des
queues Python : le moteur tourne dans un thread separe et envoie les
mises a jour via des queues que l'UI lit periodiquement (polling toutes les 100ms).
"""

import customtkinter as ctk
from datetime import datetime

from app.ui.theme import COLORS, FONTS, SIZES
from app.ui.components.stats_widget import StatsWidget
from app.ui.components.log_viewer import LogViewer
from app.core.sender_engine import SenderEngine
from app.data.models import UserProfile, Settings
from app.data.profile_manager import ProfileManager
from app.data.config_manager import ConfigManager
from app.data.history_manager import HistoryManager


class SendingFrame(ctk.CTkFrame):
    """Dashboard d'envoi avec stats, progression, logs et controles start/pause/stop."""

    def __init__(self, parent, profile_manager: ProfileManager,
                 config_manager: ConfigManager, history_manager: HistoryManager):
        """
        Args:
            parent: widget parent
            profile_manager: pour charger le profil de candidature
            config_manager: pour charger les parametres (delais, timeouts, etc.)
            history_manager: pour verifier et enregistrer les envois dans l'historique
        """
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self.profile_manager = profile_manager
        self.config_manager = config_manager
        self.history_manager = history_manager
        self.engine = SenderEngine()
        self._start_time: datetime | None = None
        self._timer_id: str | None = None

        self._build_ui()

    def _build_ui(self):
        """Construit l'interface du dashboard d'envoi."""
        # Titre
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SIZES["padding"], pady=(SIZES["padding"], 10))

        ctk.CTkLabel(header, text="Envoi des Candidatures", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).pack(side="left")

        # Boutons de controle
        ctrl_frame = ctk.CTkFrame(header, fg_color="transparent")
        ctrl_frame.pack(side="right")

        self.btn_start = ctk.CTkButton(
            ctrl_frame, text="Demarrer l'envoi", font=FONTS["button"], width=150, height=36,
            fg_color=COLORS["success"], hover_color="#16a34a",
            text_color="white", corner_radius=6, command=self._on_start,
        )
        self.btn_start.pack(side="left", padx=5)

        self.btn_pause = ctk.CTkButton(
            ctrl_frame, text="Pause", font=FONTS["button"], width=80, height=36,
            fg_color=COLORS["warning"], hover_color="#d97706",
            text_color="white", corner_radius=6, command=self._on_pause, state="disabled",
        )
        self.btn_pause.pack(side="left", padx=5)

        self.btn_stop = ctk.CTkButton(
            ctrl_frame, text="Arreter", font=FONTS["button"], width=80, height=36,
            fg_color=COLORS["error"], hover_color="#dc2626",
            text_color="white", corner_radius=6, command=self._on_stop, state="disabled",
        )
        self.btn_stop.pack(side="left", padx=5)

        # Checkbox mode test (dry run = envoi simule sans reel envoi)
        self.dry_run_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            ctrl_frame, text="Mode test", variable=self.dry_run_var,
            font=FONTS["body_small"], text_color=COLORS["text_muted"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
        ).pack(side="left", padx=(15, 0))

        # Stats
        self.stats_widget = StatsWidget(self)
        self.stats_widget.pack(fill="x", padx=SIZES["padding"], pady=(5, 10))

        # Barre de progression
        prog_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8)
        prog_frame.pack(fill="x", padx=SIZES["padding"], pady=(0, 5))

        self.progress_label = ctk.CTkLabel(
            prog_frame, text="En attente...", font=FONTS["body_small"],
            text_color=COLORS["text_muted"],
        )
        self.progress_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(
            prog_frame, height=8, fg_color=COLORS["bg_input"],
            progress_color=COLORS["accent"], corner_radius=4,
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 5))
        self.progress_bar.set(0)

        # Entreprise en cours
        self.company_label = ctk.CTkLabel(
            prog_frame, text="", font=FONTS["body_small"],
            text_color=COLORS["text_secondary"],
        )
        self.company_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Logs en bas
        ctk.CTkLabel(self, text="Evenements recents", font=FONTS["subtitle"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=SIZES["padding"], pady=(5, 5))

        self.log_viewer = LogViewer(self, height=180)
        self.log_viewer.pack(fill="both", expand=True, padx=SIZES["padding"], pady=(0, SIZES["padding"]))

    def _on_start(self):
        """Lance l'envoi des candidatures."""
        profile = self.profile_manager.load()
        if not profile.is_valid():
            self.log_viewer.add_log("error", "Profil incomplet. Remplissez tous les champs dans l'onglet Profil.")
            return

        settings = self.config_manager.load()
        dry_run = self.dry_run_var.get()

        self.stats_widget.reset()
        self.log_viewer.clear()
        self.progress_bar.set(0)

        # Creer un nouveau moteur d'envoi avec le history_manager
        # pour qu'il puisse verifier et enregistrer les envois
        self.engine = SenderEngine()
        self.engine.start(profile, settings, self.history_manager, dry_run=dry_run)

        self._start_time = datetime.now()
        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal")
        self.btn_stop.configure(state="normal")

        self.log_viewer.add_log("info", f"Envoi demarre {'(mode test)' if dry_run else ''}")
        self._poll_queues()
        self._update_timer()

    def _on_pause(self):
        """Met en pause ou reprend l'envoi."""
        if self.engine.state == "running":
            self.engine.pause()
            self.btn_pause.configure(text="Reprendre")
            self.log_viewer.add_log("info", "Envoi en pause")
        elif self.engine.state == "paused":
            self.engine.resume()
            self.btn_pause.configure(text="Pause")
            self.log_viewer.add_log("info", "Envoi repris")

    def _on_stop(self):
        """Arrete l'envoi."""
        self.engine.stop()
        self._reset_buttons()
        self.log_viewer.add_log("warning", "Arret demande")

    def _reset_buttons(self):
        """Remet les boutons dans leur etat initial."""
        self.btn_start.configure(state="normal")
        self.btn_pause.configure(state="disabled", text="Pause")
        self.btn_stop.configure(state="disabled")

    def _poll_queues(self):
        """
        Lit les queues de communication du moteur d'envoi.

        Le moteur tourne dans un thread separe et ne peut pas modifier l'UI
        directement (tkinter n'est pas thread-safe). Les queues servent
        d'intermediaire : le moteur y pousse des messages, l'UI les lit
        periodiquement (toutes les 100ms via self.after()).
        """
        done = False

        # Lire les logs
        while not self.engine.log_queue.empty():
            entry = self.engine.log_queue.get_nowait()
            if entry["message"] == "DONE":
                done = True
                self.log_viewer.add_log("info", "Envoi termine !")
            else:
                self.log_viewer.add_log(entry["level"], entry["message"], entry.get("time", ""))

        # Lire les statistiques
        while not self.engine.stats_queue.empty():
            stats = self.engine.stats_queue.get_nowait()
            self.stats_widget.update_stats(stats)

        # Lire la progression
        while not self.engine.progress_queue.empty():
            prog = self.engine.progress_queue.get_nowait()
            current, total = prog["current"], prog["total"]
            self.progress_bar.set(current / total if total > 0 else 0)
            self.progress_label.configure(text=f"{current} / {total} organisations traitees")

        # Lire l'entreprise en cours
        while not self.engine.company_queue.empty():
            company = self.engine.company_queue.get_nowait()
            status_map = {
                "en_cours": "En cours...",
                "chargement": "Chargement page...",
                "formulaire": "Remplissage formulaire...",
                "anti-bot": "Attente anti-bot...",
                "envoi": "Envoi en cours...",
                "verification": "Verification...",
                "succes": "Envoye !",
                "echec": "Echec",
                "deja_envoye": "Deja contacte (ignore)",
            }
            status_text = status_map.get(company["status"], company["status"])
            self.company_label.configure(text=f"{company['name']} - {status_text}")

        if done:
            self._reset_buttons()
            self._start_time = None
        else:
            # Re-planifier le polling dans 100ms
            self.after(100, self._poll_queues)

    def _update_timer(self):
        """Met a jour le chronometre affiche dans les stats."""
        if self._start_time is None:
            return
        elapsed = datetime.now() - self._start_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            self.stats_widget.update_temps(f"{hours}h {minutes:02d}m {seconds:02d}s")
        else:
            self.stats_widget.update_temps(f"{minutes:02d}m {seconds:02d}s")

        self._timer_id = self.after(1000, self._update_timer)
