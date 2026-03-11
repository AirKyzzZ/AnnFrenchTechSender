import customtkinter as ctk
import logging
import queue

from app.ui.theme import COLORS, FONTS, SIZES
from app.ui.components.log_viewer import LogViewer


class QueueLogHandler(logging.Handler):
    """Handler de logging qui envoie les logs dans une queue pour l'UI."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        level_map = {
            "INFO": "info",
            "WARNING": "warning",
            "ERROR": "error",
            "CRITICAL": "error",
            "DEBUG": "info",
        }
        level = level_map.get(record.levelname, "info")
        self.log_queue.put({
            "level": level,
            "message": self.format(record),
            "time": record.created,
        })


class LogsFrame(ctk.CTkFrame):
    """Visualisation des logs en temps reel depuis le fichier de logging."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_dark"])
        self._log_queue: queue.Queue = queue.Queue()

        self._build_ui()
        self._setup_handler()
        self._poll()

    def _build_ui(self):
        # Titre
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SIZES["padding"], pady=(SIZES["padding"], 10))

        ctk.CTkLabel(header, text="Journaux", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).pack(side="left")

        ctk.CTkButton(
            header, text="Effacer", font=FONTS["button"], width=80, height=36,
            fg_color=COLORS["error_bg"], hover_color=COLORS["error"],
            text_color=COLORS["error"], corner_radius=6,
            command=lambda: self.log_viewer.clear(),
        ).pack(side="right")

        # Log viewer pleine page
        self.log_viewer = LogViewer(self, height=500)
        self.log_viewer.pack(fill="both", expand=True, padx=SIZES["padding"], pady=(0, SIZES["padding"]))

    def _setup_handler(self):
        handler = QueueLogHandler(self._log_queue)
        handler.setFormatter(logging.Formatter("%(name)s - %(message)s"))
        logging.getLogger().addHandler(handler)

    def _poll(self):
        while not self._log_queue.empty():
            entry = self._log_queue.get_nowait()
            import datetime
            ts = datetime.datetime.fromtimestamp(entry["time"]).strftime("%H:%M:%S") if isinstance(entry["time"], float) else ""
            self.log_viewer.add_log(entry["level"], entry["message"], ts)

        self.after(200, self._poll)
