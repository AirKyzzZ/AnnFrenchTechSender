#!/usr/bin/env python3
"""
VERSION DEBUG VISUELLE du sender
- Affiche le navigateur Chrome (mode visible)
- Va lentement pour observer chaque étape
- Traite seulement les 3 premières entreprises
- Affiche des messages détaillés à chaque étape
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
import logging

# Configurer les logs
logging.basicConfig(
    filename='candidature_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
Maxime Mansiet
maxime.mansiet@gmail.com | 07 83 97 23 60"""
}

print("\n" + "="*70)
print("🐛 MODE DEBUG VISUEL - SENDER")
print("="*70)
print("\nCaractéristiques de ce mode :")
print("  ✓ Navigateur VISIBLE (vous voyez tout ce qui se passe)")
print("  ✓ Mode LENT (pauses entre chaque action)")
print("  ✓ Seulement 3 ENTREPRISES traitées")
print("  ✓ Messages détaillés à chaque étape")
print("\n⚠️  ATTENTION : Ce script envoie de VRAIES candidatures !")
print("="*70)

response = input("\nContinuer ? (oui/non): ")
if response.lower() != "oui":
    print("Annulé.")
    exit(0)

# Charger les 3 premières URLs
print("\n📋 Chargement des URLs...")
URLS_ENTREPRISES = []
with open("urls_entreprises.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)
    for i, row in enumerate(reader):
        if i >= 3:  # Seulement les 3 premières
            break
        URLS_ENTREPRISES.append(row[0])

print(f"✓ {len(URLS_ENTREPRISES)} entreprises à traiter :")
for i, url in enumerate(URLS_ENTREPRISES, 1):
    print(f"  {i}. {url}")

# Initialiser Chrome en mode VISIBLE
print("\n🌐 Initialisation de Chrome en mode VISIBLE...")
options = webdriver.ChromeOptions()
# PAS DE --headless ! On veut voir !
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
print("✓ Chrome ouvert et prêt !")

def pause(secondes, message=""):
    """Pause avec compte à rebours visible"""
    if message:
        print(f"\n⏸️  {message}")
    for i in range(secondes, 0, -1):
        print(f"   ... {i} seconde{'s' if i > 1 else ''}", end='\r')
        time.sleep(1)
    print("   ... ✓ C'est parti !           ")

def envoyer_candidature_debug(url, numero):
    """Envoie une candidature en mode debug"""
    print("\n" + "="*70)
    print(f"📧 ENVOI #{numero} - {url}")
    print("="*70)
    
    try:
        print(f"\n[ÉTAPE 1/7] Chargement de la page...")
        driver.get(url)
        pause(3, "Page en cours de chargement")
        print("✓ Page chargée")
        
        print(f"\n[ÉTAPE 2/7] Recherche du formulaire...")
        try:
            driver.find_element(By.NAME, "organization_contact[last_name]")
            print("✓ Formulaire trouvé !")
        except NoSuchElementException:
            print("✗ ERREUR : Formulaire non trouvé sur cette page")
            return False
        
        print(f"\n[ÉTAPE 3/7] Remplissage des champs...")
        print(f"   - Nom : {CANDIDATURE['nom']}")
        driver.find_element(By.NAME, "organization_contact[last_name]").send_keys(CANDIDATURE["nom"])
        time.sleep(0.5)
        
        print(f"   - Prénom : {CANDIDATURE['prenom']}")
        driver.find_element(By.NAME, "organization_contact[first_name]").send_keys(CANDIDATURE["prenom"])
        time.sleep(0.5)
        
        print(f"   - Email : {CANDIDATURE['email']}")
        driver.find_element(By.NAME, "organization_contact[email]").send_keys(CANDIDATURE["email"])
        time.sleep(0.5)
        
        print(f"   - Téléphone : {CANDIDATURE['telephone']}")
        driver.find_element(By.NAME, "organization_contact[phone]").send_keys(CANDIDATURE["telephone"])
        time.sleep(0.5)
        
        print(f"   - Objet : {CANDIDATURE['objet']}")
        driver.find_element(By.NAME, "organization_contact[subject]").send_keys(CANDIDATURE["objet"])
        time.sleep(0.5)
        
        print(f"   - Message : {CANDIDATURE['message'][:50]}...")
        driver.find_element(By.NAME, "organization_contact[message]").send_keys(CANDIDATURE["message"])
        print("✓ Tous les champs remplis !")
        
        pause(2, "Vérifiez visuellement que le formulaire est bien rempli")
        
        print(f"\n[ÉTAPE 4/7] URL avant soumission :")
        print(f"   {driver.current_url}")
        
        print(f"\n[ÉTAPE 5/7] Soumission du formulaire...")
        print("   Méthode : form.submit()")
        driver.find_element(By.TAG_NAME, "form").submit()
        print("✓ Formulaire soumis !")
        
        pause(5, "Attente de la réponse du serveur (5 secondes)")
        
        print(f"\n[ÉTAPE 6/7] URL après soumission :")
        print(f"   {driver.current_url}")
        
        print(f"\n[ÉTAPE 7/7] Vérification du résultat...")
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Afficher un extrait de la page
        print("\n📄 Contenu de la page (300 premiers caractères) :")
        print("-" * 70)
        print(page_text[:300])
        print("-" * 70)
        
        # Chercher le message de confirmation
        if "Votre message a bien été envoyé" in page_text:
            print("\n✅ SUCCÈS - Message de confirmation détecté !")
            print("   → La candidature a été RÉELLEMENT envoyée")
            logging.info(f"✓ SUCCÈS confirmé pour {url}")
            return True
        elif "envoyé" in page_text.lower():
            print("\n⚠️  PARTIEL - Mot 'envoyé' trouvé mais pas le message exact")
            print("   → À vérifier manuellement")
            logging.warning(f"⚠️  Résultat incertain pour {url}")
            return True
        elif "422" in page_text or "rejetée" in page_text.lower():
            print("\n❌ ÉCHEC - Erreur 422 : Soumission rejetée par le serveur")
            print("   → Le formulaire a été refusé")
            logging.error(f"✗ Erreur 422 pour {url}")
            return False
        else:
            print("\n❌ ÉCHEC - Aucun message de confirmation détecté")
            print("   → Le formulaire a été soumis mais probablement pas envoyé")
            logging.error(f"✗ Pas de confirmation pour {url}")
            return False
        
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement : {e}")
        logging.error(f"Erreur pour {url}: {e}")
        return False

# Traiter les entreprises
print("\n" + "="*70)
print("DÉBUT DU TRAITEMENT")
print("="*70)

succes = 0
echecs = 0

for i, url in enumerate(URLS_ENTREPRISES, 1):
    resultat = envoyer_candidature_debug(url, i)
    
    if resultat:
        succes += 1
        print(f"\n✅ Envoi #{i} : SUCCÈS")
    else:
        echecs += 1
        print(f"\n❌ Envoi #{i} : ÉCHEC")
    
    if i < len(URLS_ENTREPRISES):
        pause(5, f"Pause avant l'envoi suivant ({i+1}/{len(URLS_ENTREPRISES)})")

# Résumé final
print("\n" + "="*70)
print("RÉSUMÉ FINAL")
print("="*70)
print(f"Entreprises traitées : {len(URLS_ENTREPRISES)}")
print(f"Succès : {succes}")
print(f"Échecs : {echecs}")
if len(URLS_ENTREPRISES) > 0:
    print(f"Taux de réussite : {(succes/len(URLS_ENTREPRISES))*100:.0f}%")
print("="*70)

print("\n⏸️  Le navigateur reste ouvert pendant 10 secondes")
print("   Vous pouvez voir la dernière page")
time.sleep(10)

driver.quit()
print("\n✓ Navigateur fermé")
print("\n📝 Logs détaillés sauvegardés dans 'candidature_debug.log'")
print("\n" + "="*70)
