import json
import os
from app.data.models import UserProfile

PROFILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "profiles")


class ProfileManager:
    def __init__(self, profiles_dir: str = PROFILES_DIR):
        self.profiles_dir = profiles_dir
        os.makedirs(self.profiles_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        return os.path.join(self.profiles_dir, f"{name}.json")

    def save(self, profile: UserProfile, name: str = "default") -> None:
        with open(self._path(name), "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, name: str = "default") -> UserProfile:
        path = self._path(name)
        if not os.path.exists(path):
            return UserProfile()
        with open(path, "r", encoding="utf-8") as f:
            return UserProfile.from_dict(json.load(f))

    def exists(self, name: str = "default") -> bool:
        return os.path.exists(self._path(name))

    def list_profiles(self) -> list[str]:
        if not os.path.exists(self.profiles_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(self.profiles_dir) if f.endswith(".json")]

    def delete(self, name: str) -> bool:
        path = self._path(name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
