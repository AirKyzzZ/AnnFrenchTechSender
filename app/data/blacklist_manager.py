"""
blacklist_manager.py - Gestionnaire de la liste noire

La liste noire est stockee dans un fichier texte (1 URL par ligne).
C'est l'approche "NoSQL" du projet : un fichier plat sans structure
relationnelle, adapte pour une simple liste sans relations.

Pourquoi un fichier texte et pas SQLite ?
  → C'est une liste simple sans relations (pas de user_id, pas de jointures)
  → Facile a editer manuellement si necessaire
  → Permet de montrer au jury la difference SQL vs NoSQL dans le projet
"""

import os


class BlacklistManager:
    """
    Gere la liste noire des organisations a ignorer lors de l'envoi.

    Les URLs blacklistees sont exclues du processus d'envoi.
    Utile pour les entreprises qui ont deja repondu ou qu'on ne veut pas contacter.
    """

    def __init__(self, filepath: str = "blacklist.txt"):
        self.filepath = filepath

    def load(self) -> list[str]:
        if not os.path.exists(self.filepath):
            return []
        with open(self.filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]

    def save(self, urls: list[str]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write("# Liste noire des organisations a ignorer\n")
            f.write("# Format: une URL par ligne\n")
            for url in sorted(set(urls)):
                f.write(f"{url}\n")

    def add(self, url: str) -> bool:
        urls = self.load()
        if url in urls:
            return False
        urls.append(url)
        self.save(urls)
        return True

    def remove(self, url: str) -> bool:
        urls = self.load()
        if url not in urls:
            return False
        urls.remove(url)
        self.save(urls)
        return True

    def contains(self, url: str) -> bool:
        return url in self.load()

    def count(self) -> int:
        return len(self.load())

    def as_set(self) -> set[str]:
        return set(self.load())
