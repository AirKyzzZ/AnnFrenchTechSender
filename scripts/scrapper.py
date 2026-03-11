from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
import time
import csv
import logging

# Configurer les logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrapper_logs.log'),
        logging.StreamHandler()
    ]
)

# URL de base de l'annuaire
BASE_URL = "https://annuaire.frenchtechbordeaux.com/organisations?page="

# Initialiser Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Mode sans interface graphique
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def recuperer_urls_entreprises(max_pages=163):
    """
    Récupère les URLs de toutes les organisations de l'annuaire French Tech Bordeaux.
    
    Args:
        max_pages (int): Nombre maximum de pages à parcourir
    
    Returns:
        list: Liste des URLs des organisations
    """
    urls = set()
    erreurs = 0
    
    logging.info(f"Début du scraping de {max_pages - 1} pages...")
    
    for page in range(1, max_pages):
        try:
            logging.info(f"Scraping page {page}/{max_pages - 1}...")
            driver.get(BASE_URL + str(page))
            time.sleep(2)  # Attendre le chargement
            
            entreprises = driver.find_elements(By.CSS_SELECTOR, "a[href^='/organisations/']")
            urls_page = 0
            
            for entreprise in entreprises:
                url = entreprise.get_attribute("href")
                if url and url.startswith("https://annuaire.frenchtechbordeaux.com/organisations/"):
                    if url not in urls:
                        urls.add(url)
                        urls_page += 1
            
            logging.info(f"Page {page}: {urls_page} nouvelles URLs trouvées (total: {len(urls)})")
            
        except WebDriverException as e:
            erreurs += 1
            logging.error(f"Erreur lors du scraping de la page {page}: {e}")
            if erreurs > 10:
                logging.critical("Trop d'erreurs détectées. Arrêt du scraping.")
                break
        except Exception as e:
            logging.error(f"Erreur inattendue page {page}: {e}")
    
    logging.info(f"Scraping terminé. {len(urls)} URLs récupérées.")
    return sorted(list(urls))

if __name__ == "__main__":
    try:
        # Récupérer et sauvegarder les URLs
        urls_entreprises = recuperer_urls_entreprises()
        
        # Sauvegarder dans un CSV
        csv_filename = "urls_entreprises.csv"
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["URL"])
            for url in urls_entreprises:
                writer.writerow([url])
        
        logging.info(f"✓ {len(urls_entreprises)} URLs sauvegardées dans {csv_filename}")
        print(f"\n✓ Scraping terminé avec succès !")
        print(f"  - {len(urls_entreprises)} URLs récupérées")
        print(f"  - Fichier généré: {csv_filename}")
        
    except Exception as e:
        logging.critical(f"Erreur critique: {e}")
        print(f"\n✗ Erreur lors du scraping: {e}")
    finally:
        driver.quit()
        logging.info("Navigateur fermé.")