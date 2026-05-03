"""
scraper_engine.py - Moteur de scraping des URLs d'organisations

Ce module parcourt toutes les pages de l'annuaire French Tech Bordeaux
et collecte les URLs des organisations. Ces URLs sont ensuite utilisees
par le sender_engine pour envoyer les candidatures.

Le scraping se fait via Selenium : on charge chaque page de l'annuaire,
on recupere tous les liens vers les organisations, et on les sauvegarde
dans un fichier CSV.

Note : le scraping fonctionne dans un thread separe pour ne pas bloquer l'UI.
"""

import csv
import logging
import threading
import time
import queue

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

# URL de base de l'annuaire avec pagination (?page=1, ?page=2, etc.)
BASE_URL = "https://annuaire.frenchtechbordeaux.com/organisations?page="


class ScraperEngine:
    """Scrape les URLs des organisations depuis l'annuaire French Tech Bordeaux."""

    def __init__(self):
        self.log_queue: queue.Queue = queue.Queue()
        self.progress_queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, output_path: str = "urls_entreprises.csv", max_pages: int = 163):
        if self._thread and self._thread.is_alive():
            return
        self.stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(output_path, max_pages),
            daemon=True
        )
        self._thread.start()

    def stop(self):
        self.stop_event.set()

    def _log(self, level: str, message: str):
        self.log_queue.put({"level": level, "message": message})

    def _run(self, output_path: str, max_pages: int):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        urls = set()
        erreurs = 0

        self._log("info", f"Debut du scraping de {max_pages - 1} pages...")

        try:
            for page in range(1, max_pages):
                if self.stop_event.is_set():
                    break

                try:
                    driver.get(BASE_URL + str(page))
                    time.sleep(2)

                    entreprises = driver.find_elements(By.CSS_SELECTOR, "a[href^='/organisations/']")
                    urls_page = 0

                    for entreprise in entreprises:
                        url = entreprise.get_attribute("href")
                        if url and url.startswith("https://annuaire.frenchtechbordeaux.com/organisations/"):
                            if url not in urls:
                                urls.add(url)
                                urls_page += 1

                    self._log("info", f"Page {page}/{max_pages - 1}: {urls_page} nouvelles URLs (total: {len(urls)})")
                    self.progress_queue.put({"current": page, "total": max_pages - 1})

                except WebDriverException as e:
                    erreurs += 1
                    self._log("error", f"Erreur page {page}: {e}")
                    if erreurs > 10:
                        self._log("error", "Trop d'erreurs. Arret du scraping.")
                        break

            # Sauvegarder
            sorted_urls = sorted(list(urls))
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["URL"])
                for url in sorted_urls:
                    writer.writerow([url])

            self._log("success", f"Scraping termine. {len(sorted_urls)} URLs sauvegardees dans {output_path}")

        except Exception as e:
            self._log("error", f"Erreur critique: {e}")
        finally:
            driver.quit()
            self._log("info", "DONE")
