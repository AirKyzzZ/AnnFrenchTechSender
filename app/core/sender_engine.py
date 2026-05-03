"""
sender_engine.py - Moteur d'envoi des candidatures

Ce module est le coeur de l'automatisation. Il tourne dans un thread separe
pour ne pas bloquer l'interface graphique pendant l'envoi.

Fonctionnement :
  1. Charge les URLs depuis le fichier CSV
  2. Filtre les URLs deja contactees (via historique SQLite) et en blacklist
  3. Pour chaque URL : ouvre la page, remplit le formulaire, attend l'anti-bot, envoie
  4. Enregistre le resultat (succes/echec) dans l'historique SQLite
  5. Communique avec l'UI via des queues (logs, stats, progression)

Communication UI <-> Worker :
  Le moteur ne peut PAS modifier l'UI directement (tkinter n'est pas thread-safe).
  Il utilise des queues (file d'attente thread-safe) pour envoyer des messages
  a l'UI, qui les lit periodiquement via polling (cf. sending_frame.py).
"""

import csv
import logging
import threading
import time
import queue
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from app.data.models import UserProfile, Settings, SendingStats
from app.data.blacklist_manager import BlacklistManager
from app.data.history_manager import HistoryManager
from app.core.selenium_manager import SeleniumManager

logger = logging.getLogger(__name__)


class SenderEngine:
    """
    Thread worker qui gere l'envoi des candidatures.

    Communique avec l'UI via 4 queues :
      - log_queue     : messages de log (info, warning, error)
      - stats_queue   : statistiques mises a jour (envoyes, echecs, etc.)
      - progress_queue: progression (current/total)
      - company_queue : entreprise en cours de traitement
    """

    def __init__(self):
        # Queues de communication : UI <- Worker
        # Queue = file d'attente thread-safe (pas de conflit entre threads)
        self.log_queue: queue.Queue = queue.Queue()
        self.stats_queue: queue.Queue = queue.Queue()
        self.progress_queue: queue.Queue = queue.Queue()
        self.company_queue: queue.Queue = queue.Queue()

        # Evenements de controle : UI -> Worker
        # threading.Event = drapeau boleen thread-safe (set/clear/is_set)
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

        self._thread: threading.Thread | None = None
        self._selenium: SeleniumManager | None = None
        self._stats = SendingStats()
        self._state = "idle"  # idle, running, paused, stopped

    @property
    def state(self) -> str:
        return self._state

    @property
    def stats(self) -> SendingStats:
        return self._stats

    def start(self, profile: UserProfile, settings: Settings,
              history_manager: HistoryManager | None = None, dry_run: bool = False):
        """
        Demarre l'envoi dans un thread separe.

        Args:
            profile: profil de candidature (nom, email, message, etc.)
            settings: parametres (delais, timeouts, chemins fichiers)
            history_manager: gestionnaire d'historique (pour eviter les doublons)
            dry_run: si True, simule l'envoi sans ouvrir Chrome
        """
        if self._state == "running":
            return

        self.stop_event.clear()
        self.pause_event.clear()
        self._state = "running"

        # daemon=True : le thread se termine automatiquement quand l'app se ferme
        self._thread = threading.Thread(
            target=self._run,
            args=(profile, settings, history_manager, dry_run),
            daemon=True
        )
        self._thread.start()

    def pause(self):
        """Met l'envoi en pause (le thread attend que pause_event soit clear)."""
        if self._state == "running":
            self.pause_event.set()
            self._state = "paused"

    def resume(self):
        """Reprend l'envoi apres une pause."""
        if self._state == "paused":
            self.pause_event.clear()
            self._state = "running"

    def stop(self):
        """Arrete l'envoi proprement."""
        self.stop_event.set()
        self.pause_event.clear()  # Debloquer si en pause
        self._state = "stopped"

    def _log(self, level: str, message: str):
        """Envoie un message de log a l'UI via la queue."""
        self.log_queue.put({"level": level, "message": message, "time": datetime.now().strftime("%H:%M:%S")})

    def _update_stats(self):
        """Envoie les statistiques mises a jour a l'UI."""
        self.stats_queue.put(self._stats.to_dict())

    def _update_progress(self, current: int, total: int):
        """Envoie la progression a l'UI."""
        self.progress_queue.put({"current": current, "total": total})

    def _update_company(self, url: str, status: str, tentative: int = 1):
        """Envoie l'entreprise en cours a l'UI."""
        name = url.split("/organisations/")[-1] if "/organisations/" in url else url
        self.company_queue.put({"url": url, "name": name, "status": status, "tentative": tentative})

    def _load_urls(self, settings: Settings, history_manager: HistoryManager | None) -> list[str]:
        """
        Charge les URLs depuis le CSV et filtre celles deja traitees.

        Filtrage en 2 etapes :
          1. Exclure les URLs de la blacklist (organisations a ignorer)
          2. Exclure les URLs deja envoyees avec succes (via l'historique SQLite)
        """
        blacklist = BlacklistManager(settings.blacklist_path)
        blacklist_set = blacklist.as_set()

        # Charger les URLs du CSV
        urls = []
        try:
            with open(settings.csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # Sauter l'en-tete
                urls = [row[0] for row in reader if row and row[0] not in blacklist_set]
        except FileNotFoundError:
            self._log("error", f"Fichier CSV non trouve: {settings.csv_path}")

        total_csv = len(urls)

        # Filtrer les URLs deja envoyees avec succes grace a l'historique
        if history_manager:
            urls_deja_envoyees = history_manager.get_urls_envoyees()
            urls = [u for u in urls if u not in urls_deja_envoyees]
            nb_deja = total_csv - len(urls)
            if nb_deja > 0:
                self._log("info", f"{nb_deja} organisations deja contactees (ignorees)")

        self._log("info", f"{len(urls)} organisations a contacter "
                  f"(blacklist: {len(blacklist_set)}, total CSV: {total_csv})")
        return urls

    def _run(self, profile: UserProfile, settings: Settings,
             history_manager: HistoryManager | None, dry_run: bool):
        """
        Boucle principale d'envoi (tourne dans un thread separe).

        Pour chaque URL :
          1. Verifier si l'arret ou la pause ont ete demandes
          2. Envoyer la candidature via Selenium
          3. Enregistrer le resultat dans l'historique
          4. Attendre un delai aleatoire (anti-detection)
        """
        self._stats = SendingStats()
        self._stats.temps_debut = datetime.now().strftime("%H:%M:%S")

        urls = self._load_urls(settings, history_manager)
        self._stats.total = len(urls)
        self._update_stats()

        if not urls:
            self._log("error", "Aucune URL a traiter")
            self._finalize()
            return

        # Initialiser Selenium (sauf en mode test)
        if not dry_run:
            self._selenium = SeleniumManager(settings)
            try:
                self._log("info", "Initialisation de Chrome...")
                self._selenium.initialiser_driver()
                self._log("info", "Chrome demarre avec succes")
            except Exception as e:
                self._log("error", f"Impossible de demarrer Chrome: {e}")
                self._finalize()
                return

        try:
            for i, url in enumerate(urls):
                # Verifier si l'arret a ete demande
                if self.stop_event.is_set():
                    self._log("info", "Arret demande par l'utilisateur")
                    break

                # Gerer la pause : attendre que l'utilisateur reprenne
                while self.pause_event.is_set():
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.2)

                if self.stop_event.is_set():
                    break

                self._stats.en_cours = i + 1
                self._update_progress(i + 1, len(urls))
                self._update_company(url, "en_cours")
                self._log("info", f"[{i + 1}/{len(urls)}] Envoi en cours: {url.split('/organisations/')[-1]}")

                # Rotation de session Chrome si la session est trop longue
                # (change l'adresse IP/cookies pour eviter d'etre bloque)
                if not dry_run and self._selenium and self._selenium.session_expiree():
                    self._log("info", "Rotation de session Chrome...")
                    self._selenium.relancer_session("Duree de session depassee")
                    self._log("info", "Nouvelle session Chrome prete")

                # Envoyer la candidature
                success = self._envoyer_candidature(url, profile, settings, dry_run)

                if success:
                    self._stats.envoyes += 1
                    self._update_company(url, "succes")
                    self._log("success", f"Candidature envoyee: {url.split('/organisations/')[-1]}")
                    # Enregistrer le succes dans l'historique SQLite
                    if history_manager:
                        history_manager.enregistrer_envoi(url, "succes")
                else:
                    self._stats.echecs += 1
                    self._stats.echecs_urls.append(url)
                    self._update_company(url, "echec")
                    self._log("error", f"Echec de l'envoi: {url.split('/organisations/')[-1]}")
                    # Enregistrer l'echec dans l'historique
                    if history_manager:
                        history_manager.enregistrer_envoi(url, "echec")

                self._update_stats()

                # Pause entre envois (delai aleatoire pour paraitre humain)
                if not dry_run and i < len(urls) - 1:
                    pause = settings.delay_min + (settings.delay_max - settings.delay_min) * 0.5
                    time.sleep(pause)

        except Exception as e:
            self._log("error", f"Erreur critique: {e}")
            logger.exception("Erreur critique dans le worker")
        finally:
            self._finalize()

    def _envoyer_candidature(self, url: str, profile: UserProfile, settings: Settings,
                             dry_run: bool, tentative: int = 1) -> bool:
        """
        Envoie une candidature a une organisation via son formulaire de contact.

        Etapes :
          1. Charger la page de l'organisation
          2. Remplir les champs du formulaire (nom, prenom, email, etc.)
          3. Attendre que le bouton anti-bot devienne cliquable
          4. Cliquer sur le bouton d'envoi
          5. Verifier le message de confirmation

        En cas d'echec, retente jusqu'a max_tentatives (recursion).
        """
        if dry_run:
            time.sleep(0.1)
            return True

        driver = self._selenium.get_driver()

        try:
            # Charger la page
            self._update_company(url, "chargement", tentative)
            driver.get(url)
            time.sleep(2)

            # Remplir le formulaire
            # Les noms des champs (organization_contact[...]) correspondent
            # aux attributs name= dans le HTML du site French Tech Bordeaux
            self._update_company(url, "formulaire", tentative)
            driver.find_element(By.NAME, "organization_contact[last_name]").send_keys(profile.nom)
            driver.find_element(By.NAME, "organization_contact[first_name]").send_keys(profile.prenom)
            driver.find_element(By.NAME, "organization_contact[email]").send_keys(profile.email)
            driver.find_element(By.NAME, "organization_contact[phone]").send_keys(profile.telephone)
            driver.find_element(By.NAME, "organization_contact[subject]").send_keys(profile.objet)
            driver.find_element(By.NAME, "organization_contact[message]").send_keys(profile.message)

            time.sleep(1)

            # Attente du bouton anti-bot
            # Le site utilise un captcha invisible qui active le bouton apres un delai
            self._update_company(url, "anti-bot", tentative)
            self._log("info", "Attente de la verification anti-bot...")

            max_attente = settings.timeout_bouton
            temps_debut = time.time()
            bouton_pret = False

            while time.time() - temps_debut < max_attente:
                if self.stop_event.is_set():
                    return False

                try:
                    submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
                    bouton_value = submit_button.get_attribute("value")
                    est_disabled = submit_button.get_attribute("disabled")

                    # Le bouton est pret quand il n'est plus disabled
                    # et que son texte contient "envoyer" ou "envoi"
                    if est_disabled is None and ("envoyer" in bouton_value.lower() or "envoi" in bouton_value.lower()):
                        temps_ecoule = int(time.time() - temps_debut)
                        self._log("info", f"Bouton pret: '{bouton_value}' (apres {temps_ecoule}s)")
                        bouton_pret = True
                        break

                    time.sleep(2)
                except Exception:
                    time.sleep(2)

            if not bouton_pret:
                self._log("warning", f"Timeout bouton apres {max_attente}s")
                if tentative < settings.max_tentatives:
                    driver.refresh()
                    time.sleep(3)
                    self._log("info", f"Retry apres refresh (tentative {tentative + 1}/{settings.max_tentatives})")
                    return self._envoyer_candidature(url, profile, settings, dry_run, tentative + 1)
                return False

            # Clic sur le bouton d'envoi
            self._update_company(url, "envoi", tentative)
            try:
                submit_button.click()
            except Exception as e:
                self._log("error", f"Erreur clic bouton: {e}")
                return False

            time.sleep(3)

            # Verification du resultat
            self._update_company(url, "verification", tentative)
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # Erreur 422 : le formulaire a ete rejete (souvent un probleme de validation)
            if "422" in page_text:
                self._log("warning", f"Erreur 422 (tentative {tentative}/{settings.max_tentatives})")
                if tentative < settings.max_tentatives:
                    time.sleep(3)
                    return self._envoyer_candidature(url, profile, settings, dry_run, tentative + 1)
                return False

            # Message de succes du site
            if "Votre message a bien" in page_text or "bien été envoyé" in page_text:
                return True

            self._log("warning", "Pas de message de confirmation")
            return False

        except (WebDriverException, TimeoutException) as e:
            # Session Chrome invalide : reinitialiser le driver
            if "invalid session" in str(e).lower() or "session deleted" in str(e).lower():
                self._log("warning", "Session invalide, reinitialisation...")
                if tentative < settings.max_tentatives:
                    try:
                        self._selenium.initialiser_driver()
                        time.sleep(2)
                        return self._envoyer_candidature(url, profile, settings, dry_run, tentative + 1)
                    except Exception:
                        return False
            self._log("error", f"Erreur WebDriver: {e}")
            return False

        except NoSuchElementException as e:
            self._log("error", f"Element formulaire non trouve: {e}")
            return False

        except Exception as e:
            self._log("error", f"Erreur inattendue: {e}")
            return False

    def _finalize(self):
        """Nettoie les ressources a la fin de l'envoi."""
        self._stats.temps_fin = datetime.now().strftime("%H:%M:%S")
        self._update_stats()

        # Fermer Chrome proprement
        if self._selenium:
            self._selenium.fermer()
            self._selenium = None

        # Signal de fin pour l'UI
        self._log("info", "DONE")
        self._state = "idle"
