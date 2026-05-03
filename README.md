# FT Sender - French Tech Bordeaux

Application desktop pour automatiser l'envoi de candidatures de stage via les formulaires de contact de l'annuaire French Tech Bordeaux.

Projet realise dans le cadre de l'epreuve E6 du BTS SIO SLAM (EPSI Bordeaux).

## Fonctionnalites

- **Authentification locale** : Inscription et connexion avec mot de passe hashe (bcrypt)
- **Profil candidat** : Sauvegarde et modification des informations personnelles (nom, email, telephone, message de candidature)
- **Envoi automatise** : Envoi en masse avec barre de progression, statistiques temps reel et logs detailles
- **Historique des envois** : Suivi des candidatures envoyees, detection des doublons (ne renvoie pas aux entreprises deja contactees)
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

1. **Ecran de connexion** : Creez un compte (nom d'utilisateur + mot de passe) puis connectez-vous
2. **Onglet Profil** : Remplissez vos informations personnelles et votre message de candidature, puis cliquez sur "Enregistrer"
3. **Onglet Parametres** : Ajustez les delais et options si necessaire
4. **Onglet Envoi** : Cliquez sur "Demarrer l'envoi" (cochez "Mode test" pour un essai sans envoi reel)
5. **Suivi** : Observez la progression, les statistiques et les logs en temps reel

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

## Architecture du projet

```
AnnFrenchTechSender/
├── app/                           # Application desktop
│   ├── main.py                    # Point d'entree (init DB, theme, fenetre)
│   ├── core/                      # Logique metier
│   │   ├── sender_engine.py       # Moteur d'envoi (thread worker + Selenium)
│   │   ├── scraper_engine.py      # Scraping des URLs de l'annuaire
│   │   └── selenium_manager.py    # Configuration et gestion de Chrome
│   ├── data/                      # Couche donnees
│   │   ├── database.py            # Base de donnees SQLite (tables, requetes)
│   │   ├── auth_manager.py        # Authentification (bcrypt, inscription, connexion)
│   │   ├── models.py              # Modeles de donnees (User, UserProfile, Settings, Stats)
│   │   ├── profile_manager.py     # Gestion des profils (SQLite)
│   │   ├── history_manager.py     # Historique des envois (SQLite, detection doublons)
│   │   ├── blacklist_manager.py   # Liste noire (fichier TXT = NoSQL)
│   │   └── config_manager.py      # Configuration (fichier JSON = NoSQL)
│   └── ui/                        # Interface utilisateur (CustomTkinter)
│       ├── main_window.py         # Fenetre principale (login → dashboard)
│       ├── theme.py               # Theme dark-blue et constantes UI
│       ├── components/            # Composants reutilisables
│       │   ├── navigation.py      # Sidebar de navigation
│       │   ├── stats_widget.py    # Grille de statistiques
│       │   └── log_viewer.py      # Visionneuse de logs avec filtres
│       └── frames/                # Ecrans de l'application
│           ├── login_frame.py     # Connexion / Inscription
│           ├── profile_frame.py   # Formulaire de profil
│           ├── sending_frame.py   # Dashboard d'envoi
│           ├── blacklist_frame.py # Gestion de la liste noire
│           ├── logs_frame.py      # Visualisation des journaux
│           └── settings_frame.py  # Parametres de l'application
├── tests/                         # Tests automatises (pytest)
│   ├── conftest.py                # Configuration partagee des tests
│   ├── test_models.py             # Tests unitaires : modeles de donnees
│   ├── test_database.py           # Tests unitaires : base de donnees SQLite
│   ├── test_auth.py               # Tests unitaires : authentification bcrypt
│   ├── test_blacklist.py          # Tests unitaires : liste noire (NoSQL)
│   ├── test_config.py             # Tests unitaires : configuration (NoSQL)
│   ├── test_history.py            # Tests unitaires : historique des envois
│   ├── test_integration.py        # Tests d'integration : parcours complets
│   └── test_e2e.py                # Tests E2E : envoi simule avec mocks Selenium
├── scripts/                       # Scripts CLI legacy
├── data/                          # Donnees utilisateur
│   ├── ftsender.db                # Base de donnees SQLite (users, profiles, historique)
│   ├── config.json                # Configuration (NoSQL)
│   └── profiles/                  # (legacy, migre vers SQLite)
├── requirements.txt               # Dependances de production
├── requirements-dev.txt           # Dependances de developpement
└── build.spec                     # Configuration PyInstaller
```

## Choix techniques

### SQL vs NoSQL

Le projet utilise **deux approches de stockage** complementaires :

| Donnees | Stockage | Justification |
|---------|----------|---------------|
| Utilisateurs, profils, historique | **SQLite** (SQL) | Donnees relationnelles (user_id → profils, historique), requetes complexes (statistiques, filtrage), transactions |
| Liste noire | **Fichier TXT** (NoSQL) | Liste simple sans relations, editable manuellement |
| Configuration | **Fichier JSON** (NoSQL) | Paires cle/valeur sans relations, lisible par un humain |

### Securite

- **Mots de passe** : hashes avec bcrypt (sel aleatoire, 12 rounds). Jamais stockes en clair.
- **Injection SQL** : requetes parametrees avec `?` (jamais de f-strings dans les requetes SQL).
- **Messages d'erreur** : generiques pour ne pas reveler l'existence d'un compte.

### Architecture

- **Separation des responsabilites** : data/ (donnees), core/ (logique), ui/ (interface)
- **Communication thread-safe** : queues Python entre le worker d'envoi et l'interface
- **Encapsulation POO** : chaque module est une classe avec une responsabilite unique

## Tests

```bash
# Installer les dependances de developpement
pip install -r requirements-dev.txt

# Lancer tous les tests
python -m pytest tests/ -v

# Tests unitaires uniquement
python -m pytest tests/test_models.py tests/test_database.py tests/test_auth.py tests/test_blacklist.py tests/test_config.py tests/test_history.py -v

# Tests d'integration
python -m pytest tests/test_integration.py -v

# Tests E2E
python -m pytest tests/test_e2e.py -v
```

### Types de tests

| Type | Fichiers | Objectif |
|------|----------|----------|
| **Unitaires (TU)** | test_models, test_database, test_auth, test_blacklist, test_config, test_history | Tester chaque classe isolement |
| **Integration (TI)** | test_integration | Tester les interactions entre modules (auth → profil → historique) |
| **E2E (TE2E)** | test_e2e | Simuler un envoi complet avec mocks Selenium |

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
- **SQLite** - Base de donnees relationnelle (stdlib Python)
- **bcrypt** - Hachage securise des mots de passe
- **WebDriver Manager** - Gestion automatique du driver Chrome
- **pytest** - Framework de tests
- **PyInstaller** - Packaging en executable

## Historique des versions

- **Mars 2026** : Authentification, base SQLite, historique des envois, tests complets
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
