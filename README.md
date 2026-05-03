# FT Sender, French Tech Bordeaux

> Client lourd Python d'envoi automatisé de candidatures aux organisations
> de l'annuaire French Tech Bordeaux.
>
> **Réalisation professionnelle n° 2 du dossier de l'épreuve E6 du BTS SIO
> option SLAM, session 2026** (EPSI Bordeaux).

[![Python](https://img.shields.io/badge/python-3.11-blue?style=flat-square)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-green?style=flat-square)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-Educational-orange?style=flat-square)](#licence-et-responsabilité)

---

## Sommaire

- [Documentation BTS SIO E6](#documentation-bts-sio-e6)
- [Aperçu du projet](#aperçu-du-projet)
- [Fonctionnalités](#fonctionnalités)
- [Pré-requis](#pré-requis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Architecture du projet](#architecture-du-projet)
- [Choix techniques](#choix-techniques)
- [Tests](#tests)
- [Build (exécutable standalone)](#build-exécutable-standalone)
- [Technologies](#technologies)
- [Historique des versions](#historique-des-versions)
- [Licence et responsabilité](#licence-et-responsabilité)
- [Auteur](#auteur)

---

## Documentation BTS SIO E6

Documentation technique complète à l'attention de la commission d'interrogation E6.
Tout est versionné dans le dossier [`docs/`](docs/).

| Document | Contenu |
|---|---|
| [`docs/README.md`](docs/README.md) | Index de la documentation et parcours suggéré pour le jury |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Stack, architecture en trois couches, threading, communication thread-safe, choix de stockage |
| [`docs/COMPETENCES.md`](docs/COMPETENCES.md) | Mapping détaillé des trois compétences SLAM (Concevoir+dev / Maintenance / Gérer les données) avec preuves de code |
| [`docs/SECURITE.md`](docs/SECURITE.md) | Hachage bcrypt, requêtes SQL paramétrées, isolation par utilisateur, anti-détection Selenium |
| [`docs/TESTS.md`](docs/TESTS.md) | Stratégie de tests (unitaires, intégration, E2E avec mocks), commandes |
| [`docs/uml/`](docs/uml/) | Diagrammes Mermaid : cas d'utilisation, séquences (auth, envoi), classes, déploiement, MCD |

**Compétences SLAM couvertes (bloc 2 du référentiel BTS SIO 2026) :**

- ✓ **Concevoir et développer une solution applicative**, POO, threading thread-safe (queues + events), CustomTkinter, Selenium, packaging PyInstaller, tests pytest
- ✓ **Assurer la maintenance corrective ou évolutive**, Évolution CLI legacy → desktop UI, ajout authentification + SQLite + tests, anti-détection, rotation de session
- ✓ **Gérer les données**, Hybride SQL + NoSQL : SQLite (relations + agrégations), JSON (config), TXT (blacklist), choix justifié dans la documentation

## Aperçu du projet

L'envoi manuel de candidatures à plusieurs centaines d'organisations est répétitif,
chronophage et sujet aux doublons. FT Sender automatise ce processus tout en
restant **entièrement local** (aucune dépendance à un service cloud), avec
**authentification multi-utilisateur** et **historique de déduplication** pour
éviter de recontacter une organisation déjà sollicitée avec succès.

## Fonctionnalités

- **Authentification locale** : inscription et connexion avec mot de passe haché (bcrypt, 12 rounds)
- **Profil candidat** : sauvegarde et modification des informations personnelles (nom, email, téléphone, message de candidature)
- **Envoi automatisé** : envoi en masse avec barre de progression, statistiques temps réel et logs détaillés
- **Historique des envois** : suivi des candidatures envoyées, détection des doublons (ne renvoie pas aux entreprises déjà contactées avec succès)
- **Liste noire** : gestion des organisations à ignorer
- **Journaux** : visualisation des logs en temps réel avec filtres par niveau
- **Paramètres** : configuration des délais, timeouts, mode headless et chemins de fichiers
- **Anti-détection** : masquage de Selenium, user-agent réel, timing humain, rotation de session
- **Contrôle** : démarrer, mettre en pause et arrêter l'envoi à tout moment

## Pré-requis

- Python 3.10 ou supérieur (testé sur 3.11)
- Google Chrome installé sur le système
- Fichier `urls_entreprises.csv` avec les URLs des organisations (généré par le scraper)

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/AirKyzzZ/AnnFrenchTechSender.git
cd AnnFrenchTechSender

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # macOS / Linux
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### Lancer l'application desktop

```bash
python app/main.py
```

### Première utilisation

1. **Écran de connexion** : créez un compte (nom d'utilisateur + mot de passe) puis connectez-vous
2. **Onglet Profil** : remplissez vos informations personnelles et votre message de candidature, puis cliquez sur « Enregistrer »
3. **Onglet Paramètres** : ajustez les délais et options si nécessaire
4. **Onglet Envoi** : cliquez sur « Démarrer l'envoi » (cochez « Mode test » pour un essai sans envoi réel)
5. **Suivi** : observez la progression, les statistiques et les logs en temps réel

### Scraper les URLs (si nécessaire)

Si vous n'avez pas encore le fichier `urls_entreprises.csv` :

```bash
python scripts/scrapper.py
```

### Scripts CLI (legacy)

Les scripts en ligne de commande originaux sont conservés dans `scripts/` :

```bash
python scripts/sender.py                       # envoi en mode terminal
python scripts/sender.py --dry-run             # mode test sans envoi réel
python scripts/sender.py --visible             # mode visible (fenêtre Chrome)
python scripts/blacklist_manager.py list       # gestion de la liste noire
python scripts/blacklist_manager.py add <url>
python scripts/blacklist_manager.py remove <url>
```

## Architecture du projet

```
AnnFrenchTechSender/
├── app/                           # Application desktop
│   ├── main.py                    # Point d'entrée (init DB, thème, fenêtre)
│   ├── core/                      # Logique métier
│   │   ├── sender_engine.py       # Moteur d'envoi (thread worker + Selenium)
│   │   ├── scraper_engine.py      # Scraping des URLs de l'annuaire
│   │   └── selenium_manager.py    # Configuration et gestion de Chrome
│   ├── data/                      # Couche données
│   │   ├── database.py            # Base de données SQLite (tables, requêtes)
│   │   ├── auth_manager.py        # Authentification (bcrypt, inscription, connexion)
│   │   ├── models.py              # Modèles de données (User, UserProfile, Settings, Stats)
│   │   ├── profile_manager.py     # Gestion des profils (SQLite)
│   │   ├── history_manager.py     # Historique des envois (SQLite, détection doublons)
│   │   ├── blacklist_manager.py   # Liste noire (fichier TXT = NoSQL)
│   │   └── config_manager.py      # Configuration (fichier JSON = NoSQL)
│   └── ui/                        # Interface utilisateur (CustomTkinter)
│       ├── main_window.py         # Fenêtre principale (login → dashboard)
│       ├── theme.py               # Thème dark-blue et constantes UI
│       ├── components/            # Composants réutilisables
│       │   ├── navigation.py
│       │   ├── stats_widget.py
│       │   └── log_viewer.py
│       └── frames/                # Écrans de l'application
│           ├── login_frame.py
│           ├── profile_frame.py
│           ├── sending_frame.py
│           ├── blacklist_frame.py
│           ├── logs_frame.py
│           └── settings_frame.py
├── tests/                         # Tests automatisés (pytest)
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_database.py
│   ├── test_auth.py
│   ├── test_blacklist.py
│   ├── test_config.py
│   ├── test_history.py
│   ├── test_integration.py
│   └── test_e2e.py
├── scripts/                       # Scripts CLI legacy
├── docs/                          # Documentation BTS SIO E6 (voir Sommaire)
├── data/                          # Données utilisateur (gitignored)
├── requirements.txt               # Dépendances de production
├── requirements-dev.txt           # Dépendances de développement
└── build.spec                     # Configuration PyInstaller
```

## Choix techniques

### SQL vs NoSQL, hybridation justifiée

Le projet utilise **trois types de stockage** complémentaires, chacun adapté à
la nature de la donnée :

| Données | Stockage | Justification |
|---------|----------|---------------|
| Utilisateurs, profils, historique | **SQLite** (relationnel) | Clés étrangères (`user_id`), agrégations (`COUNT`, `CASE WHEN`), transactions, contraintes `UNIQUE` |
| Liste noire | **Fichier TXT** (NoSQL plat) | Liste sans relations, éditable manuellement, simple à versionner |
| Configuration | **Fichier JSON** (NoSQL document) | Paires clé/valeur sans relations, lisible par un humain |

### Sécurité

- **Mots de passe** : hachés avec **bcrypt** (sel aléatoire, 12 rounds). Jamais stockés en clair.
- **Injection SQL** : requêtes paramétrées (`?`) systématiquement, jamais de `f-string` dans le SQL.
- **Messages d'erreur** : génériques pour ne pas révéler l'existence d'un compte.
- **Isolation par utilisateur** : tous les `SELECT` filtrent par `user_id`.

### Architecture

- **Séparation des responsabilités** : `data/` (persistance), `core/` (logique métier), `ui/` (interface)
- **Communication thread-safe** : 4 queues + 2 events entre le worker d'envoi et l'IHM
- **Encapsulation POO** : chaque module est une classe avec une responsabilité unique

## Tests

```bash
# Installer les dépendances de développement
pip install -r requirements-dev.txt

# Lancer tous les tests
python -m pytest tests/ -v
```

| Type | Fichiers | Objectif |
|------|----------|----------|
| **Unitaires (TU)** | `test_models`, `test_database`, `test_auth`, `test_blacklist`, `test_config`, `test_history` | Tester chaque classe en isolation |
| **Intégration (TI)** | `test_integration` | Tester les interactions entre modules (auth → profil → historique) |
| **E2E (TE2E)** | `test_e2e` | Simuler un envoi complet avec mocks Selenium |

Voir [`docs/TESTS.md`](docs/TESTS.md) pour le détail.

## Build (exécutable standalone)

```bash
pip install -r requirements-dev.txt
pyinstaller build.spec
```

L'exécutable est généré dans le dossier `dist/`.

## Technologies

- **Python 3.11**, langage principal
- **CustomTkinter**, interface graphique moderne
- **Selenium** + **WebDriver Manager**, automatisation du navigateur
- **SQLite**, base de données relationnelle (stdlib Python)
- **bcrypt**, hachage sécurisé des mots de passe
- **pytest**, framework de tests
- **PyInstaller**, packaging en exécutable autonome
- **Git / GitHub**, versionnage et suivi des problèmes

## Historique des versions

| Période | Évolution |
|---|---|
| **Mars 2026** | Authentification, base SQLite, historique de déduplication, suite de tests complète |
| **Février 2026** | Refonte en application desktop CustomTkinter (interface graphique) |
| **Octobre 2025** | Ajout de la liste noire, amélioration des logs |
| **Février 2025** | Version initiale (CLI dans `scripts/`) |

## Licence et responsabilité

Ce projet est fourni à des fins éducatives dans le cadre d'un projet de classe
(BTS SIO, EPSI Bordeaux). L'utilisateur est seul responsable de son utilisation.
Assurez-vous de respecter les conditions d'utilisation du site French Tech Bordeaux.

## Auteur

**Maxime Louis François Mansiet**, étudiant BTS SIO à l'EPSI Bordeaux

- Portfolio : [maximemansiet.fr](https://maximemansiet.fr)
- GitHub : [@AirKyzzZ](https://github.com/AirKyzzZ)
- LinkedIn : [maxime-mansiet](https://linkedin.com/in/maxime-mansiet)
