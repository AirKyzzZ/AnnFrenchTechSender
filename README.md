# FT Sender - French Tech Bordeaux

Application desktop pour automatiser l'envoi de candidatures de stage via les formulaires de contact de l'annuaire French Tech Bordeaux.

## Fonctionnalites

- **Profil candidat** : Sauvegarde et modification des informations personnelles (nom, email, telephone, message de candidature)
- **Envoi automatise** : Envoi en masse avec barre de progression, statistiques temps reel et logs detailles
- **Liste noire** : Gestion des organisations a ignorer (deja contactees ou ayant repondu)
- **Journaux** : Visualisation des logs en temps reel avec filtres par niveau
- **Parametres** : Configuration des delais, timeouts, mode headless et chemins de fichiers
- **Anti-detection** : Masquage de Selenium, user-agent reel, timing humain
- **Controle** : Demarrer, mettre en pause et arreter l'envoi a tout moment

## Prerequis

- Python 3.10 ou superieur
- Google Chrome installe sur le systeme
- Fichier `urls_entreprises.csv` avec les URLs des organisations (genere par le scraper)

## Installation

```bash
# Cloner le depot
git clone <url-du-depot>
cd AnnFrenchTechSender

# Creer un environnement virtuel
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou: venv\Scripts\activate  # Windows

# Installer les dependances
pip install -r requirements.txt
```

## Utilisation

### Lancer l'application desktop

```bash
python app/main.py
```

### Premiere utilisation

1. **Onglet Profil** : Remplissez vos informations personnelles et votre message de candidature, puis cliquez sur "Enregistrer"
2. **Onglet Parametres** : Ajustez les delais et options si necessaire
3. **Onglet Envoi** : Cliquez sur "Demarrer l'envoi" (cochez "Mode test" pour un essai sans envoi reel)
4. **Suivi** : Observez la progression, les statistiques et les logs en temps reel

### Scraper les URLs (si necessaire)

Si vous n'avez pas encore le fichier `urls_entreprises.csv` :

```bash
python scripts/scrapper.py
```

### Scripts CLI (legacy)

Les scripts en ligne de commande originaux sont conserves dans le dossier `scripts/` :

```bash
# Envoi en mode terminal
python scripts/sender.py

# Mode test (sans envoi reel)
python scripts/sender.py --dry-run

# Mode visible (avec fenetre Chrome)
python scripts/sender.py --visible

# Gestion de la liste noire
python scripts/blacklist_manager.py list
python scripts/blacklist_manager.py add <url>
python scripts/blacklist_manager.py remove <url>
```

## Structure du projet

```
AnnFrenchTechSender/
├── app/                        # Application desktop
│   ├── main.py                 # Point d'entree
│   ├── core/                   # Logique metier
│   │   ├── sender_engine.py    # Moteur d'envoi (thread worker)
│   │   ├── scraper_engine.py   # Scraping des URLs
│   │   └── selenium_manager.py # Gestion de Chrome/Selenium
│   ├── data/                   # Couche donnees
│   │   ├── models.py           # Modeles (UserProfile, Settings, Stats)
│   │   ├── profile_manager.py  # Gestion des profils JSON
│   │   ├── blacklist_manager.py# Gestion de la liste noire
│   │   └── config_manager.py   # Parametres de l'application
│   └── ui/                     # Interface utilisateur
│       ├── main_window.py      # Fenetre principale
│       ├── theme.py            # Theme et constantes UI
│       ├── components/         # Composants reutilisables
│       └── frames/             # Ecrans de l'application
├── scripts/                    # Scripts CLI legacy
├── data/                       # Donnees utilisateur
│   └── profiles/               # Profils candidat (JSON)
├── requirements.txt            # Dependances
├── requirements-dev.txt        # Dependances de developpement
└── build.spec                  # Configuration PyInstaller
```

## Build (executable standalone)

```bash
# Installer les dependances de developpement
pip install -r requirements-dev.txt

# Construire l'executable
pyinstaller build.spec
```

L'executable sera genere dans le dossier `dist/`.

## Technologies

- **Python 3.11** - Langage principal
- **CustomTkinter** - Interface graphique moderne
- **Selenium** - Automatisation du navigateur
- **WebDriver Manager** - Gestion automatique du driver Chrome
- **PyInstaller** - Packaging en executable

## Historique des versions

- **Fevrier 2026** : Application desktop avec interface graphique (CustomTkinter)
- **Octobre 2025** : Ajout de la liste noire, amelioration des logs
- **Fevrier 2025** : Version initiale (CLI)

## Licence et responsabilite

Ce projet est fourni a des fins educatives dans le cadre d'un projet de classe (BTS SIO, EPSI Bordeaux). L'utilisateur est seul responsable de son utilisation. Assurez-vous de respecter les conditions d'utilisation du site French Tech Bordeaux.

## Auteur

**Maxime Mansiet** - Etudiant BTS SIO a l'EPSI Bordeaux
- Portfolio : [maximemansiet.fr](https://maximemansiet.fr)
- GitHub : [airkyzzz](https://github.com/airkyzzz)
- LinkedIn : [maxime-mansiet](https://linkedin.com/in/maxime-mansiet)
