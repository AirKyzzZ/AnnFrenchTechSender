import logging
import time
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

from app.data.models import Settings

logger = logging.getLogger(__name__)


class SeleniumManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.driver = None
        self.heure_debut_session = None

    def initialiser_driver(self) -> webdriver.Chrome:
        self.fermer()

        options = webdriver.ChromeOptions()

        if self.settings.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--start-maximized")

        # Stabilite
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")

        # Anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)

        # User agent reel
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        options.page_load_strategy = "normal"

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(self.settings.timeout_page)

        # Masquer les proprietes JavaScript de detection Selenium
        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self.heure_debut_session = datetime.now()
        logger.info(f"Driver Selenium initialise - Session demarree a {self.heure_debut_session.strftime('%H:%M:%S')}")

        return self.driver

    def fermer(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver ferme")
            except Exception:
                pass
            self.driver = None

    def session_expiree(self) -> bool:
        if not self.settings.rotation_active or not self.heure_debut_session:
            return False
        minutes = (datetime.now() - self.heure_debut_session).total_seconds() / 60
        return minutes >= self.settings.duree_session_minutes

    def relancer_session(self, raison: str = ""):
        logger.info(f"Relance session Chrome - Raison: {raison}")
        self.fermer()
        pause = random.randint(8, 15)
        time.sleep(pause)
        self.initialiser_driver()

    def get_driver(self) -> webdriver.Chrome:
        if self.driver is None:
            self.initialiser_driver()
        return self.driver

    @staticmethod
    def delai_humain(min_sec: float = 0.5, max_sec: float = 2.0):
        time.sleep(random.uniform(min_sec, max_sec))

    @staticmethod
    def scroller_vers(driver, element):
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element
        )
        time.sleep(random.uniform(0.3, 0.7))

    @staticmethod
    def bouger_souris_vers(driver, element):
        ActionChains(driver).move_to_element(element).perform()
        time.sleep(random.uniform(0.1, 0.3))
