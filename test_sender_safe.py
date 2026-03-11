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
from datetime import datetime, timedelta

# Mode test : mettez à True pour simuler sans envoyer réellement
DRY_RUN = "--dry-run" in sys.argv or "--test" in sys.argv
TEST_5 = "--test-5" in sys.argv  # Traiter seulement 5 entreprises
MODE_VISIBLE = "--visible" in sys.argv  # Mode visible (avec fenêtre Chrome)

# Paramètres de rotation du navigateur (anti-détection)
# DÉSACTIVÉ : La rotation n'est pas nécessaire, le timing humain suffit
ROTATION_ACTIVE = False  # Mettre à True pour réactiver la rotation automatique
DUREE_SESSION_MINUTES = 15  # Durée d'une session avant de relancer Chrome
PAUSE_ENTRE_SESSIONS_MINUTES = 4  # Pause de 4 minutes entre chaque session

# Configurer les logs
logging.basicConfig(
    filename='candidature_logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if DRY_RUN:
    print("[!] MODE TEST ACTIVE - Aucune candidature ne sera reellement envoyee\n")

if not MODE_VISIBLE:
    print("[MODE ARRIERE-PLAN] Chrome tourne en arriere-plan (headless)")
    print("   > Vous pouvez eteindre votre ecran ou faire autre chose")
    print("   > Utilisez '--visible' pour voir Chrome en action")
    print("\n[IMPORTANT] Pour ecran debranche :")
    print("   > Verifiez que Windows ne met pas l'ordinateur en veille")
    print("   > Parametres > Systeme > Alimentation > Mise en veille : Jamais\n")

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
    print("[!] MODE TEST-5 : Seulement 5 entreprises seront traitees\n")

logging.info(f"{len(URLS_ENTREPRISES)} organisations à contacter (après filtrage de la liste noire).")

# Variables globales pour le driver et la session
driver = None
heure_debut_session = None

def initialiser_driver():
    """
    Initialise ou réinitialise le driver Selenium.
    Retourne une instance du driver Chrome.
    """
    global driver, heure_debut_session
    
    # Fermer le driver existant s'il y en a un
    if driver:
        try:
            driver.quit()
            logging.info("Driver précédent fermé")
        except:
            pass
    
    options = webdriver.ChromeOptions()
    
    # Mode headless (arrière-plan) par défaut, sauf si --visible est spécifié
    if not MODE_VISIBLE:
        options.add_argument("--headless=new")  # Mode headless (pas de fenêtre)
        options.add_argument("--window-size=1920,1080")  # Taille de fenêtre virtuelle
        print("   [MODE ARRIERE-PLAN] Mode arriere-plan active (headless)")
        logging.info("Chrome lancé en mode headless (arrière-plan)")
    else:
        options.add_argument("--start-maximized")  # Fenêtre maximisée pour mieux voir
        print("   [MODE VISIBLE] Mode visible active (avec fenetre Chrome)")
        logging.info("Chrome lancé en mode visible")
    
    # Options essentielles pour stabilité
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Options critiques pour fonctionner quand l'écran est débranché
    options.add_argument("--disable-gpu")  # Désactiver le GPU (utiliser le rendu logiciel)
    options.add_argument("--disable-software-rasterizer")  # Éviter les problèmes de rendu
    options.add_argument("--disable-extensions")  # Pas d'extensions
    options.add_argument("--disable-setuid-sandbox")  # Stabilité supplémentaire
    
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
    
    # Initialiser l'heure de début de session
    heure_debut_session = datetime.now()
    
    logging.info(f"Driver Selenium initialisé avec succès (mode humain) - Session démarrée à {heure_debut_session.strftime('%H:%M:%S')}")
    return driver

# Fonctions pour mimer un comportement humain
def delai_humain(min_sec=0.5, max_sec=2.0):
    """Pause aléatoire pour mimer un humain"""
    time.sleep(random.uniform(min_sec, max_sec))

def taper_comme_humain(element, texte):
    """Tape du texte lettre par lettre avec des délais aléatoires - VERSION LENTE"""
    element.click()  # Cliquer d'abord sur le champ
    time.sleep(random.uniform(0.3, 0.7))  # Réflexion avant de commencer à taper
    
    for i, char in enumerate(texte):
        element.send_keys(char)
        
        # Délai variable : vraiment imiter un humain qui tape
        if random.random() < 0.15:  # 15% du temps, pause plus longue (réflexion)
            time.sleep(random.uniform(0.3, 0.6))
        elif random.random() < 0.05:  # 5% du temps, très longue pause (chercher un mot)
            time.sleep(random.uniform(0.8, 1.5))
        else:
            time.sleep(random.uniform(0.05, 0.15))  # Frappe normale
        
        # Petite pause tous les 10-15 caractères (respiration)
        if i > 0 and i % random.randint(10, 15) == 0:
            time.sleep(random.uniform(0.2, 0.5))

def bouger_souris_vers(driver, element):
    """Bouge la souris vers un élément de façon naturelle"""
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    time.sleep(random.uniform(0.1, 0.3))

def scroller_vers(driver, element):
    """Scroll jusqu'à un élément de façon naturelle"""
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
    time.sleep(random.uniform(0.3, 0.7))

def forcer_relance_session(raison=""):
    """
    Force une relance immédiate de la session Chrome (en cas de blocage détecté).
    """
    global driver, heure_debut_session
    
    print(f"\n{'='*60}")
    print(f"[RELANCE] RELANCE FORCEE DE CHROME")
    if raison:
        print(f"Raison : {raison}")
    print(f"{'='*60}\n")
    logging.info(f"Relance forcée de Chrome - Raison: {raison}")
    
    # Fermer le navigateur actuel
    if driver:
        try:
            driver.quit()
            logging.info("Navigateur fermé (relance forcée)")
        except:
            pass
    
    # Pause courte mais suffisante pour contourner la détection
    pause_secondes = random.randint(8, 15)
    print(f"[PAUSE] Pause de {pause_secondes} secondes pour contourner la detection...")
    time.sleep(pause_secondes)
    
    # Relancer un nouveau navigateur
    print(f"[CHROME] Lancement d'une nouvelle instance de Chrome...")
    initialiser_driver()
    print(f"[OK] Nouveau navigateur pret !\n")

def verifier_et_relancer_session():
    """
    Vérifie si la session actuelle dépasse la durée autorisée.
    Si oui, ferme le navigateur, prend une pause, et relance une nouvelle session.
    """
    global driver, heure_debut_session
    
    if heure_debut_session is None:
        return  # Pas encore de session
    
    temps_ecoule = datetime.now() - heure_debut_session
    minutes_ecoulees = temps_ecoule.total_seconds() / 60
    
    if minutes_ecoulees >= DUREE_SESSION_MINUTES:
        print(f"\n{'='*60}")
        print(f"[SESSION] Session en cours depuis {minutes_ecoulees:.1f} minutes")
        print(f"[RELANCE] Relance d'une nouvelle instance de Chrome pour eviter la detection")
        print(f"{'='*60}\n")
        logging.info(f"Rotation du navigateur après {minutes_ecoulees:.1f} minutes d'utilisation")
        
        # Fermer le navigateur actuel
        if driver:
            try:
                driver.quit()
                logging.info("Navigateur fermé pour rotation")
            except:
                pass
        
        # Pause de 4 minutes pour simuler un comportement humain
        print(f"[PAUSE] Pause de {PAUSE_ENTRE_SESSIONS_MINUTES} minutes pour eviter la detection...")
        for i in range(PAUSE_ENTRE_SESSIONS_MINUTES, 0, -1):
            print(f"   [TIMER] {i} minute{'s' if i > 1 else ''} restante{'s' if i > 1 else ''}...", end='\r')
            time.sleep(60)  # Pause de 1 minute
        print(f"\n   [OK] Pause terminee !\n")
        logging.info(f"Pause de {PAUSE_ENTRE_SESSIONS_MINUTES} minutes terminée")
        
        # Relancer un nouveau navigateur
        print(f"[CHROME] Lancement d'une nouvelle instance de Chrome...")
        initialiser_driver()
        print(f"[OK] Nouveau navigateur pret !\n")

# Initialiser Selenium (sauf en mode test)
if not DRY_RUN:
    driver = initialiser_driver()

def envoyer_candidature(url, tentative=1, max_tentatives=5):
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
        print(f"   > Chargement de la page...")
        driver.get(url)
        time.sleep(2)  # Attendre que la page charge

        # Remplir le formulaire RAPIDEMENT
        print(f"   > Remplissage du formulaire...")
        
        driver.find_element(By.NAME, "organization_contact[last_name]").send_keys(CANDIDATURE["nom"])
        driver.find_element(By.NAME, "organization_contact[first_name]").send_keys(CANDIDATURE["prenom"])
        driver.find_element(By.NAME, "organization_contact[email]").send_keys(CANDIDATURE["email"])
        driver.find_element(By.NAME, "organization_contact[phone]").send_keys(CANDIDATURE["telephone"])
        driver.find_element(By.NAME, "organization_contact[subject]").send_keys(CANDIDATURE["objet"])
        driver.find_element(By.NAME, "organization_contact[message]").send_keys(CANDIDATURE["message"])
        
        print(f"   [OK] Formulaire rempli")
        time.sleep(1)  # Petite pause après remplissage
        
        # ÉTAPE CRITIQUE : Attendre que le bouton soit prêt ("Envoyer" et non disabled)
        print(f"   > Attente de la verification anti-bot...")
        
        max_attente = 240  # 4 minutes maximum
        temps_debut_attente = time.time()
        bouton_pret = False
        
        while time.time() - temps_debut_attente < max_attente:
            try:
                submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
                
                # Vérifier l'attribut value du bouton
                bouton_value = submit_button.get_attribute("value")
                est_disabled = submit_button.get_attribute("disabled")
                
                temps_ecoule = int(time.time() - temps_debut_attente)
                # Formater avec une largeur fixe pour éviter les problèmes d'affichage après 100s
                print(f"   [TIMER] {temps_ecoule:3d}s - Bouton: '{bouton_value}' | Disabled: {est_disabled is not None}".ljust(100), end='\r')
                
                # Le bouton est prêt si le texte est "Envoyer" OU si disabled=False
                if est_disabled is None and ("envoyer" in bouton_value.lower() or "envoi" in bouton_value.lower()):
                    print(f"\n   [OK] Bouton pret : '{bouton_value}' (apres {temps_ecoule}s)")
                    bouton_pret = True
                    break
                
                # Attendre 2 secondes avant de revérifier
                time.sleep(2)
                
            except Exception as e:
                print(f"\n   [!] Erreur lors de la verification du bouton : {e}")
                time.sleep(2)
        
        if not bouton_pret:
            # Le bouton n'est pas devenu prêt après 4 minutes
            print(f"\n   [ERREUR] Le bouton n'est pas devenu 'Envoyer' apres {max_attente}s")
            print(f"   [REFRESH] Refresh de la page et nouvelle tentative...")
            logging.warning(f"Timeout d'attente du bouton pour {url} - Refresh nécessaire")
            
            if tentative < max_tentatives:
                # Refresh la page (pas besoin de relancer Chrome)
                driver.refresh()
                time.sleep(3)
                print(f"   [RETRY] Nouvelle tentative apres refresh (tentative {tentative + 1}/{max_tentatives})...")
                return envoyer_candidature(url, tentative + 1, max_tentatives)
            else:
                print(f"   [ECHEC] Echec apres {max_tentatives} tentatives")
                logging.error(f"Échec après {max_tentatives} tentatives pour {url}")
                return False
        
        # Le bouton est prêt, on peut cliquer
        try:
            print(f"   > Clic sur le bouton d'envoi...")
            submit_button.click()
        except Exception as e:
            print(f"   [!] Erreur lors du clic : {e}")
            return False
        
        print(f"   > Attente de la reponse du serveur...")
        time.sleep(3)  # Attente de la réponse

        # VÉRIFIER le résultat : chercher le message de confirmation OU l'erreur 422
        print(f"   > Verification du resultat...")
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Vérifier s'il y a une erreur 422
        if "422" in page_text:
            print(f"   [!] ERREUR 422 detectee (tentative {tentative}/{max_tentatives})")
            logging.warning(f"⚠️  Erreur 422 pour {url} (tentative {tentative}/{max_tentatives})")
            
            # Si c'est la première tentative, on réessaye (souvent le 2ème envoi passe)
            if tentative < max_tentatives:
                print(f"   > Nouvelle tentative dans 3 secondes...")
                logging.info(f"→ Nouvelle tentative après erreur 422...")
                time.sleep(3)  # Pause avant de réessayer
                return envoyer_candidature(url, tentative + 1, max_tentatives)
            else:
                print(f"   [ECHEC] Erreur 422 persistante")
                logging.error(f"✗ Erreur 422 persistante après {max_tentatives} tentatives pour {url}")
                return False
        
        # Vérifier le message de confirmation
        if "Votre message a bien été envoyé" in page_text or "bien été envoyé" in page_text:
            print(f"   [OK] MESSAGE DE CONFIRMATION DETECTE !")
            logging.info(f"✓ Candidature CONFIRMÉE avec succès à {url}")
            return True
        else:
            # Pas d'erreur 422 mais pas de confirmation non plus
            print(f"   [!] Aucun message de confirmation trouve")
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
print(f"\n{'='*60}")
print(f"Debut de l'envoi des candidatures")
print(f"{'='*60}")
print(f"[STATS] Organisations : {len(URLS_ENTREPRISES)} a contacter")
print(f"[BLACKLIST] Liste noire : {len(BLACKLIST)} ignorees")
print(f"\n[MODE] Mode RAPIDE + ATTENTE INTELLIGENTE :")
print(f"   > Remplissage ultra-rapide du formulaire (~3 secondes)")
print(f"   > Attente automatique que le bouton devienne 'Envoyer'")
print(f"   > Maximum 5 tentatives par entreprise (avec refresh)")
print(f"   > Pas de comportement humain superflu (gain de temps)")
if not MODE_VISIBLE:
    print(f"\n[CONSEIL] Le script tourne en arriere-plan")
    print(f"   > Vous pouvez minimiser cette fenetre")
    print(f"   > Consultez 'candidature_logs.log' pour le suivi detaille")
print(f"\n[TEMPS] Temps estime :")
print(f"   - Si verification rapide (10-20s) : ~25s par candidature")
print(f"   - Si verification lente (1-2 min) : ~2-3 min par candidature")
print(f"   - Total pour {len(URLS_ENTREPRISES)} : Variable (depend du site)")
print(f"\n{'='*60}\n")

# Compteurs de statistiques
succes = 0
echecs = 0
echecs_liste = []

try:
    for i, url in enumerate(URLS_ENTREPRISES, 1):
        # Vérifier et relancer une nouvelle session si nécessaire (toutes les 15 minutes)
        # DÉSACTIVÉ : Le timing humain suffit, pas besoin de rotation
        if ROTATION_ACTIVE and not DRY_RUN:
            verifier_et_relancer_session()
        
        print(f"[{i}/{len(URLS_ENTREPRISES)}] Envoi en cours...")
        
        if envoyer_candidature(url):
            succes += 1
            print(f"[OK] Candidature envoyee avec succes a {url}")
        else:
            echecs += 1
            echecs_liste.append(url)
            print(f"[ERREUR] Erreur lors de l'envoi a {url}")
        
        # Petite pause entre chaque envoi (juste pour ne pas surcharger)
        time.sleep(2)
        print()
        
        # Afficher les statistiques tous les 10 envois
        if i % 10 == 0:
            print(f"\n--- Statistiques intermediaires ---")
            print(f"Succes: {succes} | Echecs: {echecs} | Total traite: {i}/{len(URLS_ENTREPRISES)}")
            if i > 0:
                print(f"Taux de reussite: {(succes/i)*100:.1f}%\n")

except KeyboardInterrupt:
    print("\n\n[!] Interruption detectee par l'utilisateur")
    logging.warning("Arrêt demandé par l'utilisateur")
    
except Exception as e:
    print(f"\n\n[ERREUR CRITIQUE] Erreur critique: {e}")
    logging.critical(f"Erreur critique dans la boucle principale: {e}")

finally:
    # Afficher les statistiques finales
    print(f"\n{'='*50}")
    print(f"STATISTIQUES FINALES")
    print(f"{'='*50}")
    print(f"Total traite: {succes + echecs}/{len(URLS_ENTREPRISES)}")
    print(f"Succes: {succes}")
    print(f"Echecs: {echecs}")
    
    if succes + echecs > 0:
        print(f"Taux de reussite: {(succes/(succes+echecs))*100:.1f}%")
    
    if echecs > 0:
        print(f"\n[!] {echecs} echecs detectes. URLs concernees:")
        for url_echec in echecs_liste[:10]:  # Afficher max 10
            print(f"  - {url_echec}")
        if len(echecs_liste) > 10:
            print(f"  ... et {len(echecs_liste) - 10} autres")
    
    if DRY_RUN:
        print(f"\n[OK] Test termine ! {len(URLS_ENTREPRISES)} candidatures auraient ete envoyees.")
        print("\nPour envoyer reellement les candidatures, executez:")
        print("  python sender.py")
    else:
        print(f"\n[OK] Envoi termine !")
    
    print(f"{'='*50}\n")
    
    # Sauvegarder les échecs dans un fichier si nécessaire
    if echecs > 0 and not DRY_RUN:
        with open("echecs_candidatures.txt", "w") as f:
            f.write("# URLs des candidatures ayant échoué\n")
            f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total: {echecs} échecs\n\n")
            for url_echec in echecs_liste:
                f.write(f"{url_echec}\n")
        print(f"[FICHIER] Liste des echecs sauvegardee dans 'echecs_candidatures.txt'\n")
    
    # Fermer le navigateur
    if driver:
        try:
            driver.quit()
            logging.info("Navigateur fermé proprement")
        except:
            pass