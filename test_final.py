#!/usr/bin/env python3
"""
Test final : envoi réel sur 3 entreprises pour valider le fix
ATTENTION : Ce test envoie de VRAIES candidatures !
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import logging

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Paramètres du candidat
CANDIDATURE = {
    "nom": "TEST",
    "prenom": "Test",
    "email": "test@test.com",  # EMAIL DE TEST
    "telephone": "0600000000",
    "objet": "Test candidature",
    "message": "Ceci est un test - merci d'ignorer ce message"
}

print("🧪 TEST FINAL - Envoi sur 3 entreprises")
print("⚠️  ATTENTION : Ce test envoie de VRAIES candidatures !")
print("   (avec des informations de TEST)")
print("\n" + "="*60)

response = input("\nContinuer ? (oui/non): ")
if response.lower() != "oui":
    print("Test annulé.")
    exit(0)

# Charger 3 URLs de test
test_urls = []
with open("urls_entreprises.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)
    for i, row in enumerate(reader):
        if i >= 3:
            break
        test_urls.append(row[0])

print(f"\n📋 {len(test_urls)} entreprises à tester:")
for url in test_urls:
    print(f"  - {url}")

# Initialiser le driver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

driver = init_driver()

# Fonction d'envoi (identique à sender.py)
def tester_envoi(url):
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        
        # Gérer les cookies
        try:
            time.sleep(2)
            cookie_button = driver.find_element(By.ID, "accepter-les-cookies")
            if cookie_button.is_displayed():
                cookie_button.click()
                time.sleep(1)
        except:
            pass
        
        # Remplir le formulaire
        nom_field = wait.until(EC.presence_of_element_located((By.NAME, "organization_contact[last_name]")))
        nom_field.clear()
        nom_field.send_keys(CANDIDATURE["nom"])
        
        driver.find_element(By.NAME, "organization_contact[first_name]").clear()
        driver.find_element(By.NAME, "organization_contact[first_name]").send_keys(CANDIDATURE["prenom"])
        
        driver.find_element(By.NAME, "organization_contact[email]").clear()
        driver.find_element(By.NAME, "organization_contact[email]").send_keys(CANDIDATURE["email"])
        
        driver.find_element(By.NAME, "organization_contact[phone]").clear()
        driver.find_element(By.NAME, "organization_contact[phone]").send_keys(CANDIDATURE["telephone"])
        
        driver.find_element(By.NAME, "organization_contact[subject]").clear()
        driver.find_element(By.NAME, "organization_contact[subject]").send_keys(CANDIDATURE["objet"])
        
        driver.find_element(By.NAME, "organization_contact[message]").clear()
        driver.find_element(By.NAME, "organization_contact[message]").send_keys(CANDIDATURE["message"])
        
        # Cliquer sur le bouton submit
        try:
            submit_button = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(0.5)
            submit_button.click()
        except NoSuchElementException:
            form = driver.find_element(By.TAG_NAME, "form")
            form.submit()
        
        # Attendre la confirmation
        try:
            confirmation = wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Votre message a bien été envoyé') or contains(text(), 'bien été envoyé')]"))
            )
            
            if confirmation.is_displayed():
                return True, "Confirmation reçue"
            else:
                return False, "Confirmation non visible"
        except TimeoutException:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "422" in page_text or "rejetée" in page_text.lower():
                return False, "Erreur 422 - Rejeté par le serveur"
            else:
                return False, "Pas de confirmation"
    
    except Exception as e:
        return False, f"Erreur: {str(e)[:100]}"

# Tester les envois
print("\n" + "="*60)
print("DÉBUT DES TESTS")
print("="*60)

succes = 0
echecs = 0

for i, url in enumerate(test_urls, 1):
    print(f"\n[{i}/{len(test_urls)}] Test de {url}")
    
    resultat, message = tester_envoi(url)
    
    if resultat:
        succes += 1
        print(f"   ✅ SUCCÈS - {message}")
    else:
        echecs += 1
        print(f"   ❌ ÉCHEC - {message}")
    
    # Pause entre les envois
    if i < len(test_urls):
        print(f"   Pause de 8 secondes...")
        time.sleep(8)

# Résultats
driver.quit()

print("\n" + "="*60)
print("RÉSULTATS DU TEST")
print("="*60)
print(f"Succès: {succes}/{len(test_urls)}")
print(f"Échecs: {echecs}/{len(test_urls)}")

if succes == len(test_urls):
    print("\n✅ TEST RÉUSSI - Le fix fonctionne parfaitement !")
    print("   Vous pouvez maintenant lancer le script complet:")
    print("   python sender.py")
elif succes > 0:
    print(f"\n⚠️  TEST PARTIEL - {succes}/{len(test_urls)} réussis")
    print("   Le fix fonctionne mais il peut y avoir des échecs occasionnels.")
else:
    print("\n❌ TEST ÉCHOUÉ - Aucun envoi réussi")
    print("   Il faut investiguer davantage.")

print("="*60)
