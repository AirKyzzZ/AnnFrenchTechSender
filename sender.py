from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import logging
import sys
import random

# Mode test : mettez à True pour simuler sans envoyer réellement
DRY_RUN = "--dry-run" in sys.argv or "--test" in sys.argv
TEST_5 = "--test-5" in sys.argv  # Traiter seulement 5 entreprises

# Configurer les logs
logging.basicConfig(
    filename='candidature_logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if DRY_RUN:
    print("⚠️  MODE TEST ACTIVÉ - Aucune candidature ne sera réellement envoyée\n")

# Paramètres du candidat
CANDIDATURE = {
    "nom": "Mansiet",
    "prenom": "Maxime",
    "email": "maxime.mansiet@gmail.com",
    "telephone": "07 83 97 23 60",
    "objet": "Candidature stage développement – Janvier 2026",
    "message": """Bonjour,

Je me permets de vous contacter dans le cadre de ma recherche de stage. Actuellement en deuxième année de BTS SIO à l'EPSI Bordeaux, je suis à la recherche d'un stage de 6 semaines à partir de janvier 2026 dans le domaine du développement web et logiciel.

Passionné par l'informatique depuis plusieurs années, j'ai déjà eu l'occasion de travailler sur de nombreux projets concrets, aussi bien en freelance (via mon agence Klyx) qu'à travers des stages précédents. Ces expériences m'ont permis de développer des compétences solides et variées, allant du front-end (React, Next.js, Tailwind) au back-end (Python/Flask, Node.js, PHP, SQL), sans oublier l'intégration d'APIs et la gestion de projet via Git.

Je me considère comme un profil polyvalent et curieux, capable de m'adapter à différents environnements techniques et d'apporter de la valeur rapidement, que ce soit sur des interfaces utilisateur, des bases de données ou des outils internes.

Vous trouverez plus d'informations sur mon travail et mes réalisations via mes profils :
- Portfolio : https://maximemansiet.fr
- GitHub : https://github.com/airkyzzz
- LinkedIn : https://linkedin.com/in/maxime-mansiet

Je serais ravi d'échanger avec vous pour voir comment je pourrais contribuer à vos projets.

Merci de votre attention, et au plaisir d'échanger.

Cordialement,
Maxime Mansiet"""
}

# Charger la liste noire
BLACKLIST = set()
try:
    with open("blacklist.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                BLACKLIST.add(line)
    logging.info(f"{len(BLACKLIST)} organisations en liste noire chargées.")
except FileNotFoundError:
    logging.warning("Fichier blacklist.txt non trouvé. Aucune organisation ne sera ignorée.")

# Charger les URLs depuis le CSV
URLS_ENTREPRISES = []
with open("urls_entreprises.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)  # Sauter l'en-tête
    URLS_ENTREPRISES = [row[0] for row in reader if row[0] not in BLACKLIST]

# Limiter à 5 si mode test-5
if TEST_5:
    URLS_ENTREPRISES = URLS_ENTREPRISES[:5]
    print("⚠️  MODE TEST-5 : Seulement 5 entreprises seront traitées\n")

logging.info(f"{len(URLS_ENTREPRISES)} organisations à contacter (après filtrage de la liste noire).")

# Variable globale pour le driver
driver = None

def initialiser_driver():
    """
    Initialise ou réinitialise le driver Selenium.
    Retourne une instance du driver Chrome.
    """
    global driver
    
    # Fermer le driver existant s'il y en a un
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # MODE VISIBLE pour debug
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")  # Fenêtre maximisée pour mieux voir
    
    # MASQUER que c'est Selenium (anti-détection bot)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent réel (pas celui de Selenium)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    options.page_load_strategy = 'normal'
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)  # Timeout de 30 secondes pour le chargement
    
    # Masquer les propriétés JavaScript qui détectent Selenium
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    logging.info("Driver Selenium initialisé avec succès (mode humain)")
    return driver

# Fonctions pour mimer un comportement humain
def delai_humain(min_sec=0.5, max_sec=2.0):
    """Pause aléatoire pour mimer un humain"""
    time.sleep(random.uniform(min_sec, max_sec))

def taper_comme_humain(element, texte):
    """Tape du texte lettre par lettre avec des délais aléatoires"""
    element.click()  # Cliquer d'abord sur le champ
    time.sleep(random.uniform(0.1, 0.3))
    
    for char in texte:
        element.send_keys(char)
        # Délai variable : parfois rapide, parfois lent
        if random.random() < 0.1:  # 10% du temps, pause plus longue
            time.sleep(random.uniform(0.1, 0.3))
        else:
            time.sleep(random.uniform(0.02, 0.08))

def bouger_souris_vers(driver, element):
    """Bouge la souris vers un élément de façon naturelle"""
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    time.sleep(random.uniform(0.1, 0.3))

def scroller_vers(driver, element):
    """Scroll jusqu'à un élément de façon naturelle"""
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
    time.sleep(random.uniform(0.3, 0.7))

# Initialiser Selenium (sauf en mode test)
if not DRY_RUN:
    driver = initialiser_driver()

def envoyer_candidature(url, tentative=1, max_tentatives=3):
    """
    Envoie une candidature à une organisation.
    En mode DRY_RUN, simule l'envoi sans réellement envoyer.
    
    Args:
        url (str): URL de l'organisation
        tentative (int): Numéro de la tentative actuelle
        max_tentatives (int): Nombre maximum de tentatives
    
    Returns:
        bool: True si succès, False sinon
    """
    global driver
    
    if DRY_RUN:
        # Mode test : simuler l'envoi
        logging.info(f"[TEST] Candidature simulée pour {url}")
        time.sleep(0.1)  # Petite pause pour simuler
        return True
    
    try:
        # Charger la page
        print(f"   → Chargement de la page...")
        driver.get(url)
        delai_humain(2, 4)  # Délai aléatoire comme un humain qui regarde la page
        
        # Scroller un peu pour mimer la lecture de la page
        driver.execute_script("window.scrollTo(0, 300);")
        delai_humain(0.5, 1.5)
        
        # Gérer la pop-up de cookies si elle apparaît
        print(f"   → Vérification pop-up cookies...")
        try:
            cookie_button = driver.find_element(By.ID, "accepter-les-cookies")
            if cookie_button.is_displayed():
                bouger_souris_vers(driver, cookie_button)
                cookie_button.click()
                print(f"   ✓ Pop-up cookies acceptée")
                logging.info(f"Pop-up cookies acceptée pour {url}")
                delai_humain(0.5, 1)
        except NoSuchElementException:
            pass  # Pas de pop-up, c'est OK
        except Exception:
            pass  # Erreur ignorée

        # Scroller jusqu'au formulaire
        print(f"   → Recherche du formulaire...")
        form = driver.find_element(By.TAG_NAME, "form")
        scroller_vers(driver, form)
        delai_humain(0.5, 1)

        # Remplir les champs du formulaire COMME UN HUMAIN
        print(f"   → Remplissage du formulaire (comme un humain)...")
        
        # Nom
        nom_field = driver.find_element(By.NAME, "organization_contact[last_name]")
        scroller_vers(driver, nom_field)
        bouger_souris_vers(driver, nom_field)
        taper_comme_humain(nom_field, CANDIDATURE["nom"])
        delai_humain(0.3, 0.8)
        
        # Prénom
        prenom_field = driver.find_element(By.NAME, "organization_contact[first_name]")
        bouger_souris_vers(driver, prenom_field)
        taper_comme_humain(prenom_field, CANDIDATURE["prenom"])
        delai_humain(0.3, 0.8)
        
        # Email
        email_field = driver.find_element(By.NAME, "organization_contact[email]")
        bouger_souris_vers(driver, email_field)
        taper_comme_humain(email_field, CANDIDATURE["email"])
        delai_humain(0.3, 0.8)
        
        # Téléphone
        tel_field = driver.find_element(By.NAME, "organization_contact[phone]")
        bouger_souris_vers(driver, tel_field)
        taper_comme_humain(tel_field, CANDIDATURE["telephone"])
        delai_humain(0.3, 0.8)
        
        # Objet
        objet_field = driver.find_element(By.NAME, "organization_contact[subject]")
        bouger_souris_vers(driver, objet_field)
        taper_comme_humain(objet_field, CANDIDATURE["objet"])
        delai_humain(0.5, 1.2)
        
        # Message (plus long, donc on tape normalement mais avec des pauses)
        message_field = driver.find_element(By.NAME, "organization_contact[message]")
        scroller_vers(driver, message_field)
        bouger_souris_vers(driver, message_field)
        message_field.click()
        delai_humain(0.2, 0.5)
        # Pour le message, on tape par morceaux pour aller plus vite mais rester naturel
        message_field.send_keys(CANDIDATURE["message"])
        delai_humain(0.5, 1.5)
        
        print(f"   ✓ Formulaire rempli")
        
        # Chercher le bouton submit
        print(f"   → Recherche du bouton d'envoi...")
        try:
            submit_button = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
            scroller_vers(driver, submit_button)
            bouger_souris_vers(driver, submit_button)
            delai_humain(0.5, 1.5)  # Hésitation avant de cliquer
            print(f"   → Clic sur le bouton d'envoi...")
            submit_button.click()
        except NoSuchElementException:
            print(f"   → Bouton non trouvé, utilisation de form.submit()...")
            form.submit()
        
        print(f"   → Attente de la réponse du serveur...")
        delai_humain(3, 5)  # Attente avec délai aléatoire

        # VÉRIFIER le résultat : chercher le message de confirmation OU l'erreur 422
        print(f"   → Vérification du résultat...")
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Vérifier s'il y a une erreur 422
        if "422" in page_text:
            print(f"   ⚠️  ERREUR 422 détectée (tentative {tentative}/{max_tentatives})")
            logging.warning(f"⚠️  Erreur 422 pour {url} (tentative {tentative}/{max_tentatives})")
            
            # Si c'est la première tentative, on réessaye (souvent le 2ème envoi passe)
            if tentative < max_tentatives:
                print(f"   → Nouvelle tentative dans 3 secondes...")
                logging.info(f"→ Nouvelle tentative après erreur 422...")
                time.sleep(3)  # Pause avant de réessayer
                return envoyer_candidature(url, tentative + 1, max_tentatives)
            else:
                print(f"   ✗ Erreur 422 persistante")
                logging.error(f"✗ Erreur 422 persistante après {max_tentatives} tentatives pour {url}")
                return False
        
        # Vérifier le message de confirmation
        if "Votre message a bien été envoyé" in page_text or "bien été envoyé" in page_text:
            print(f"   ✓ MESSAGE DE CONFIRMATION DÉTECTÉ !")
            logging.info(f"✓ Candidature CONFIRMÉE avec succès à {url}")
            return True
        else:
            # Pas d'erreur 422 mais pas de confirmation non plus
            print(f"   ⚠️  Aucun message de confirmation trouvé")
            print(f"   Extrait de la page : {page_text[:150]}...")
            logging.warning(f"⚠️  Résultat incertain pour {url} - Pas de message de confirmation clair")
            # On considère comme un échec car pas de confirmation
            return False
        
    except (WebDriverException, TimeoutException) as e:
        # Erreur de session ou de timeout - tenter de recréer le driver
        if "invalid session id" in str(e).lower() or "session deleted" in str(e).lower():
            logging.warning(f"Session invalide détectée pour {url}. Tentative {tentative}/{max_tentatives}")
            
            if tentative < max_tentatives:
                logging.info(f"Réinitialisation du driver et nouvelle tentative...")
                try:
                    initialiser_driver()
                    time.sleep(2)  # Pause après réinitialisation
                    return envoyer_candidature(url, tentative + 1, max_tentatives)
                except Exception as reinit_error:
                    logging.error(f"Erreur lors de la réinitialisation du driver: {reinit_error}")
                    return False
            else:
                logging.error(f"Échec après {max_tentatives} tentatives pour {url}: {e}")
                return False
        else:
            logging.error(f"Erreur WebDriver pour {url}: {e}")
            return False
            
    except NoSuchElementException as e:
        logging.error(f"Élément de formulaire non trouvé pour {url}: {e}")
        return False
        
    except Exception as e:
        logging.error(f"Erreur inattendue lors de l'envoi à {url}: {e}")
        return False

# Parcourir la liste des entreprises et envoyer les candidatures
print(f"\nDébut de l'envoi des candidatures...")
print(f"{len(URLS_ENTREPRISES)} organisations à contacter")
print(f"{len(BLACKLIST)} organisations en liste noire (ignorées)\n")

# Compteurs de statistiques
succes = 0
echecs = 0
echecs_liste = []

try:
    for i, url in enumerate(URLS_ENTREPRISES, 1):
        print(f"[{i}/{len(URLS_ENTREPRISES)}] Envoi en cours...")
        
        if envoyer_candidature(url):
            succes += 1
            print(f"✓ Candidature envoyée avec succès à {url}")
        else:
            echecs += 1
            echecs_liste.append(url)
            print(f"✗ Erreur lors de l'envoi à {url}")
        
        # Pause entre chaque envoi
        time.sleep(5)
        
        # Afficher les statistiques tous les 10 envois
        if i % 10 == 0:
            print(f"\n--- Statistiques intermédiaires ---")
            print(f"Succès: {succes} | Échecs: {echecs} | Total traité: {i}/{len(URLS_ENTREPRISES)}")
            if i > 0:
                print(f"Taux de réussite: {(succes/i)*100:.1f}%\n")

except KeyboardInterrupt:
    print("\n\n⚠️  Interruption détectée par l'utilisateur")
    logging.warning("Arrêt demandé par l'utilisateur")
    
except Exception as e:
    print(f"\n\n✗ Erreur critique: {e}")
    logging.critical(f"Erreur critique dans la boucle principale: {e}")

finally:
    # Afficher les statistiques finales
    print(f"\n{'='*50}")
    print(f"STATISTIQUES FINALES")
    print(f"{'='*50}")
    print(f"Total traité: {succes + echecs}/{len(URLS_ENTREPRISES)}")
    print(f"Succès: {succes}")
    print(f"Échecs: {echecs}")
    
    if succes + echecs > 0:
        print(f"Taux de réussite: {(succes/(succes+echecs))*100:.1f}%")
    
    if echecs > 0:
        print(f"\n⚠️  {echecs} échecs détectés. URLs concernées:")
        for url_echec in echecs_liste[:10]:  # Afficher max 10
            print(f"  - {url_echec}")
        if len(echecs_liste) > 10:
            print(f"  ... et {len(echecs_liste) - 10} autres")
    
    if DRY_RUN:
        print(f"\n✓ Test terminé ! {len(URLS_ENTREPRISES)} candidatures auraient été envoyées.")
        print("\nPour envoyer réellement les candidatures, exécutez:")
        print("  python sender.py")
    else:
        print(f"\n✓ Envoi terminé !")
    
    print(f"{'='*50}\n")
    
    # Sauvegarder les échecs dans un fichier si nécessaire
    if echecs > 0 and not DRY_RUN:
        with open("echecs_candidatures.txt", "w") as f:
            f.write("# URLs des candidatures ayant échoué\n")
            f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total: {echecs} échecs\n\n")
            for url_echec in echecs_liste:
                f.write(f"{url_echec}\n")
        print(f"📝 Liste des échecs sauvegardée dans 'echecs_candidatures.txt'\n")
    
    # Fermer le navigateur
    if driver:
        try:
            driver.quit()
            logging.info("Navigateur fermé proprement")
        except:
            pass