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
from app.core.selenium_manager import SeleniumManager

logger = logging.getLogger(__name__)


class SenderEngine:
    """Thread worker qui gere l'envoi des candidatures et communique avec l'UI via des queues."""

    def __init__(self):
        # Queues de communication UI <- Worker
        self.log_queue: queue.Queue = queue.Queue()
        self.stats_queue: queue.Queue = queue.Queue()
        self.progress_queue: queue.Queue = queue.Queue()
        self.company_queue: queue.Queue = queue.Queue()

        # Evenements de controle UI -> Worker
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

    def start(self, profile: UserProfile, settings: Settings, dry_run: bool = False):
        if self._state == "running":
            return

        self.stop_event.clear()
        self.pause_event.clear()
        self._state = "running"

        self._thread = threading.Thread(
            target=self._run,
            args=(profile, settings, dry_run),
            daemon=True
        )
        self._thread.start()

    def pause(self):
        if self._state == "running":
            self.pause_event.set()
            self._state = "paused"

    def resume(self):
        if self._state == "paused":
            self.pause_event.clear()
            self._state = "running"

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()  # Debloquer si en pause
        self._state = "stopped"

    def _log(self, level: str, message: str):
        self.log_queue.put({"level": level, "message": message, "time": datetime.now().strftime("%H:%M:%S")})

    def _update_stats(self):
        self.stats_queue.put(self._stats.to_dict())

    def _update_progress(self, current: int, total: int):
        self.progress_queue.put({"current": current, "total": total})

    def _update_company(self, url: str, status: str, tentative: int = 1):
        name = url.split("/organisations/")[-1] if "/organisations/" in url else url
        self.company_queue.put({"url": url, "name": name, "status": status, "tentative": tentative})

    def _load_urls(self, settings: Settings) -> list[str]:
        blacklist = BlacklistManager(settings.blacklist_path)
        blacklist_set = blacklist.as_set()

        urls = []
        try:
            with open(settings.csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # Sauter l'en-tete
                urls = [row[0] for row in reader if row and row[0] not in blacklist_set]
        except FileNotFoundError:
            self._log("error", f"Fichier CSV non trouve: {settings.csv_path}")

        self._log("info", f"{len(urls)} organisations a contacter (apres filtrage liste noire: {len(blacklist_set)})")
        return urls

    def _run(self, profile: UserProfile, settings: Settings, dry_run: bool):
        self._stats = SendingStats()
        self._stats.temps_debut = datetime.now().strftime("%H:%M:%S")

        urls = self._load_urls(settings)
        self._stats.total = len(urls)
        self._update_stats()

        if not urls:
            self._log("error", "Aucune URL a traiter")
            self._finalize()
            return

        # Init Selenium (sauf dry run)
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
                # Verifier arret
                if self.stop_event.is_set():
                    self._log("info", "Arret demande par l'utilisateur")
                    break

                # Gerer pause
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

                # Rotation session si necessaire
                if not dry_run and self._selenium and self._selenium.session_expiree():
                    self._log("info", "Rotation de session Chrome...")
                    self._selenium.relancer_session("Duree de session depassee")
                    self._log("info", "Nouvelle session Chrome prete")

                # Envoyer
                success = self._envoyer_candidature(url, profile, settings, dry_run)

                if success:
                    self._stats.envoyes += 1
                    self._update_company(url, "succes")
                    self._log("success", f"Candidature envoyee: {url.split('/organisations/')[-1]}")
                else:
                    self._stats.echecs += 1
                    self._stats.echecs_urls.append(url)
                    self._update_company(url, "echec")
                    self._log("error", f"Echec de l'envoi: {url.split('/organisations/')[-1]}")

                self._update_stats()

                # Pause entre envois
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
            self._update_company(url, "formulaire", tentative)
            driver.find_element(By.NAME, "organization_contact[last_name]").send_keys(profile.nom)
            driver.find_element(By.NAME, "organization_contact[first_name]").send_keys(profile.prenom)
            driver.find_element(By.NAME, "organization_contact[email]").send_keys(profile.email)
            driver.find_element(By.NAME, "organization_contact[phone]").send_keys(profile.telephone)
            driver.find_element(By.NAME, "organization_contact[subject]").send_keys(profile.objet)
            driver.find_element(By.NAME, "organization_contact[message]").send_keys(profile.message)

            time.sleep(1)

            # Attente bouton anti-bot
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

            # Clic envoi
            self._update_company(url, "envoi", tentative)
            try:
                submit_button.click()
            except Exception as e:
                self._log("error", f"Erreur clic bouton: {e}")
                return False

            time.sleep(3)

            # Verification resultat
            self._update_company(url, "verification", tentative)
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # Erreur 422
            if "422" in page_text:
                self._log("warning", f"Erreur 422 (tentative {tentative}/{settings.max_tentatives})")
                if tentative < settings.max_tentatives:
                    time.sleep(3)
                    return self._envoyer_candidature(url, profile, settings, dry_run, tentative + 1)
                return False

            # Succes
            if "Votre message a bien" in page_text or "bien été envoyé" in page_text:
                return True

            self._log("warning", "Pas de message de confirmation")
            return False

        except (WebDriverException, TimeoutException) as e:
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
        self._stats.temps_fin = datetime.now().strftime("%H:%M:%S")
        self._update_stats()

        if self._selenium:
            self._selenium.fermer()
            self._selenium = None

        self._log("info", "DONE")
        self._state = "idle"
