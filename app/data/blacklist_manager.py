import os


class BlacklistManager:
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
