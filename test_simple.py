#!/usr/bin/env python3
"""
Test SIMPLE pour voir ce qui se passe après la soumission
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

print("🔍 Test simple de soumission\n")

# URL de test
test_url = "https://annuaire.frenchtechbordeaux.com/organisations/10h11"

# Initialiser Chrome (NON headless pour voir)
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Désactivé pour voir ce qui se passe
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    print(f"1. Chargement de {test_url}")
    driver.get(test_url)
    time.sleep(3)
    
    print("2. Remplissage du formulaire")
    driver.find_element(By.NAME, "organization_contact[last_name]").send_keys("TEST")
    driver.find_element(By.NAME, "organization_contact[first_name]").send_keys("Test")
    driver.find_element(By.NAME, "organization_contact[email]").send_keys("test@test.com")
    driver.find_element(By.NAME, "organization_contact[phone]").send_keys("0600000000")
    driver.find_element(By.NAME, "organization_contact[subject]").send_keys("Test")
    driver.find_element(By.NAME, "organization_contact[message]").send_keys("Message de test")
    
    print("3. URL AVANT submit:")
    print(f"   {driver.current_url}")
    
    print("\n4. Soumission du formulaire (form.submit)...")
    driver.find_element(By.TAG_NAME, "form").submit()
    
    print("5. Attente de 5 secondes...")
    time.sleep(5)
    
    print("\n6. URL APRÈS submit:")
    print(f"   {driver.current_url}")
    
    print("\n7. Recherche du message de confirmation...")
    page_text = driver.find_element(By.TAG_NAME, "body").text
    
    # Chercher le message
    if "Votre message a bien été envoyé" in page_text:
        print("   ✅ MESSAGE DE CONFIRMATION TROUVÉ !")
        print("   → L'envoi a RÉELLEMENT réussi")
    elif "envoyé" in page_text.lower():
        print("   ⚠️  Texte 'envoyé' trouvé mais pas le message exact")
    else:
        print("   ❌ AUCUN MESSAGE DE CONFIRMATION")
        print("   → Le formulaire a été SOUMIS mais probablement PAS ENVOYÉ")
    
    # Afficher un extrait
    print("\n8. Extrait de la page (500 premiers caractères):")
    print("-" * 60)
    print(page_text[:500])
    print("-" * 60)
    
    print("\n\n⏸️  Le navigateur reste ouvert pendant 30 secondes")
    print("   Vous pouvez voir l'état de la page")
    print("   Le script se fermera automatiquement après...\n")
    time.sleep(30)
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("\n✓ Navigateur fermé")
