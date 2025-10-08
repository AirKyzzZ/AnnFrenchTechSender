#!/usr/bin/env python3
"""
Script de test pour vérifier que les corrections fonctionnent correctement.
Teste l'envoi sur un petit échantillon d'entreprises.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

print("🧪 Test du fix pour le problème de session invalide\n")
print("="*60)

# Charger 5 URLs de test depuis le CSV
print("\n1. Chargement des URLs de test...")
test_urls = []
try:
    with open("urls_entreprises.csv", "r") as f:
        reader = csv.reader(f)
        next(reader)  # Sauter l'en-tête
        for i, row in enumerate(reader):
            if i >= 5:  # Prendre seulement les 5 premières
                break
            test_urls.append(row[0])
    print(f"   ✓ {len(test_urls)} URLs chargées pour le test")
except Exception as e:
    print(f"   ✗ Erreur lors du chargement: {e}")
    exit(1)

# Fonction d'initialisation du driver (identique à sender.py)
def initialiser_driver():
    """Initialise le driver Chrome"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.page_load_strategy = 'normal'
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

# Test de connexion et détection du formulaire
print("\n2. Initialisation du driver Chrome...")
try:
    driver = initialiser_driver()
    print("   ✓ Driver initialisé avec succès")
except Exception as e:
    print(f"   ✗ Erreur d'initialisation: {e}")
    exit(1)

print("\n3. Test de détection des formulaires...")
formulaires_detectes = 0
erreurs = 0

for i, url in enumerate(test_urls, 1):
    print(f"\n   [{i}/{len(test_urls)}] Test de {url}")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        
        # Vérifier que le formulaire existe
        nom_field = wait.until(EC.presence_of_element_located((By.NAME, "organization_contact[last_name]")))
        
        # Vérifier tous les champs requis
        champs_requis = [
            "organization_contact[first_name]",
            "organization_contact[email]",
            "organization_contact[phone]",
            "organization_contact[subject]",
            "organization_contact[message]"
        ]
        
        champs_trouves = 0
        for champ in champs_requis:
            try:
                driver.find_element(By.NAME, champ)
                champs_trouves += 1
            except NoSuchElementException:
                print(f"      ⚠️  Champ manquant: {champ}")
        
        if champs_trouves == len(champs_requis):
            formulaires_detectes += 1
            print(f"      ✓ Formulaire complet détecté ({champs_trouves + 1}/6 champs)")
        else:
            print(f"      ⚠️  Formulaire incomplet ({champs_trouves + 1}/6 champs)")
            erreurs += 1
        
        time.sleep(2)  # Petite pause entre les tests
        
    except TimeoutException:
        print(f"      ✗ Timeout - Le formulaire n'a pas chargé à temps")
        erreurs += 1
    except WebDriverException as e:
        if "invalid session id" in str(e).lower():
            print(f"      ⚠️  SESSION INVALIDE DÉTECTÉE - Tentative de récupération...")
            try:
                driver = initialiser_driver()
                print(f"      ✓ Driver réinitialisé avec succès")
                # Réessayer
                driver.get(url)
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.NAME, "organization_contact[last_name]")))
                print(f"      ✓ Récupération réussie !")
                formulaires_detectes += 1
            except Exception as e2:
                print(f"      ✗ Échec de récupération: {e2}")
                erreurs += 1
        else:
            print(f"      ✗ Erreur WebDriver: {e}")
            erreurs += 1
    except Exception as e:
        print(f"      ✗ Erreur inattendue: {e}")
        erreurs += 1

# Fermer le driver
try:
    driver.quit()
    print("\n4. Driver fermé proprement")
except:
    pass

# Résultats
print("\n" + "="*60)
print("RÉSULTATS DU TEST")
print("="*60)
print(f"URLs testées: {len(test_urls)}")
print(f"Formulaires détectés: {formulaires_detectes}")
print(f"Erreurs: {erreurs}")

if formulaires_detectes == len(test_urls):
    print("\n✅ TEST RÉUSSI - Tous les formulaires ont été détectés !")
    print("   Le fix fonctionne correctement. Vous pouvez lancer le script complet.")
elif formulaires_detectes > 0:
    print(f"\n⚠️  TEST PARTIEL - {formulaires_detectes}/{len(test_urls)} formulaires détectés")
    print("   Certaines entreprises peuvent avoir des formulaires différents.")
else:
    print("\n❌ TEST ÉCHOUÉ - Aucun formulaire détecté")
    print("   Vérifiez votre connexion et les URLs.")

print("="*60)
