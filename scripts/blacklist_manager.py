#!/usr/bin/env python3
"""
Gestionnaire de liste noire pour French Tech Bordeaux Sender
Permet d'ajouter, supprimer et afficher les organisations en liste noire
"""

import sys

BLACKLIST_FILE = "blacklist.txt"

def load_blacklist():
    """Charge la liste noire depuis le fichier"""
    try:
        with open(BLACKLIST_FILE, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return []

def save_blacklist(urls):
    """Sauvegarde la liste noire dans le fichier"""
    with open(BLACKLIST_FILE, "w") as f:
        f.write("# Liste noire des organisations à ignorer (déjà contactées ou ayant répondu)\n")
        f.write("# Format: une URL par ligne\n")
        for url in sorted(urls):
            f.write(f"{url}\n")

def add_to_blacklist(url):
    """Ajoute une URL à la liste noire"""
    urls = load_blacklist()
    if url in urls:
        print(f"⚠️  L'URL est déjà dans la liste noire: {url}")
        return False
    urls.append(url)
    save_blacklist(urls)
    print(f"✓ URL ajoutée à la liste noire: {url}")
    return True

def remove_from_blacklist(url):
    """Retire une URL de la liste noire"""
    urls = load_blacklist()
    if url not in urls:
        print(f"⚠️  L'URL n'est pas dans la liste noire: {url}")
        return False
    urls.remove(url)
    save_blacklist(urls)
    print(f"✓ URL retirée de la liste noire: {url}")
    return True

def show_blacklist():
    """Affiche toutes les URLs de la liste noire"""
    urls = load_blacklist()
    if not urls:
        print("📋 La liste noire est vide.")
        return
    
    print(f"📋 Liste noire ({len(urls)} organisations):")
    print("-" * 80)
    for i, url in enumerate(urls, 1):
        org_name = url.split("/organisations/")[-1] if "/organisations/" in url else url
        print(f"{i:3}. {org_name}")
        print(f"     {url}")
    print("-" * 80)

def show_usage():
    """Affiche l'aide d'utilisation"""
    print("""
Gestionnaire de liste noire - French Tech Bordeaux Sender

Usage:
    python blacklist_manager.py [commande] [arguments]

Commandes:
    list                                    Afficher la liste noire
    add <url>                               Ajouter une URL à la liste noire
    remove <url>                            Retirer une URL de la liste noire
    help                                    Afficher cette aide

Exemples:
    python blacklist_manager.py list
    python blacklist_manager.py add https://annuaire.frenchtechbordeaux.com/organisations/exemple
    python blacklist_manager.py remove https://annuaire.frenchtechbordeaux.com/organisations/exemple
""")

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        show_blacklist()
    elif command == "add":
        if len(sys.argv) < 3:
            print("❌ Erreur: URL manquante")
            print("Usage: python blacklist_manager.py add <url>")
            return
        url = sys.argv[2]
        add_to_blacklist(url)
    elif command == "remove":
        if len(sys.argv) < 3:
            print("❌ Erreur: URL manquante")
            print("Usage: python blacklist_manager.py remove <url>")
            return
        url = sys.argv[2]
        remove_from_blacklist(url)
    elif command == "help":
        show_usage()
    else:
        print(f"❌ Commande inconnue: {command}")
        show_usage()

if __name__ == "__main__":
    main()

