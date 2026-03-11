import customtkinter as ctk
from app.ui.theme import COLORS, SIZES
from app.ui.components.navigation import Navigation
from app.ui.frames.profile_frame import ProfileFrame
from app.ui.frames.sending_frame import SendingFrame
from app.ui.frames.blacklist_frame import BlacklistFrame
from app.ui.frames.logs_frame import LogsFrame
from app.ui.frames.settings_frame import SettingsFrame
from app.data.profile_manager import ProfileManager
from app.data.blacklist_manager import BlacklistManager
from app.data.config_manager import ConfigManager


class MainWindow(ctk.CTk):
    """Fenetre principale avec sidebar + zone de contenu."""

    def __init__(self):
        super().__init__()

        self.title("FT Sender - French Tech Bordeaux")
        self.geometry(f"{SIZES['window_width']}x{SIZES['window_height']}")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_dark"])

        # Managers
        self.profile_manager = ProfileManager()
        self.config_manager = ConfigManager()
        settings = self.config_manager.load()
        self.blacklist_manager = BlacklistManager(settings.blacklist_path)

        # Layout principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.navigation = Navigation(self, on_navigate=self._show_frame)
        self.navigation.grid(row=0, column=0, sticky="ns")

        # Content area
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Frames
        self.frames: dict[str, ctk.CTkFrame] = {}
        self._create_frames()

        # Afficher le profil par defaut
        self._show_frame("profile")

    def _create_frames(self):
        self.frames["profile"] = ProfileFrame(self.content, self.profile_manager)
        self.frames["sending"] = SendingFrame(self.content, self.profile_manager, self.config_manager)
        self.frames["blacklist"] = BlacklistFrame(self.content, self.blacklist_manager)
        self.frames["logs"] = LogsFrame(self.content)
        self.frames["settings"] = SettingsFrame(self.content, self.config_manager)

    def _show_frame(self, key: str):
        # Cacher tous les frames
        for frame in self.frames.values():
            frame.grid_forget()

        # Afficher le frame demande
        self.frames[key].grid(row=0, column=0, sticky="nsew")
