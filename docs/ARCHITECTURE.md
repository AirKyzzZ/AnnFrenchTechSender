# Architecture technique — FT Sender

> Documentation orientée jury — épreuve E6 BTS SIO SLAM, session 2026.

## 1. Vue d'ensemble

FT Sender est un **client lourd** Python multiplateforme qui automatise l'envoi de candidatures
de stage via les formulaires de contact des organisations de l'annuaire French Tech Bordeaux.

L'application est mono-utilisateur, **entièrement locale** (aucune dépendance à un service cloud)
et conçue pour être **packagée en exécutable autonome** via PyInstaller.

```
┌──────────────────────────────────────────────────────────┐
│                  Interface graphique (Tkinter)           │
│  Login → Profil → Envoi → Logs → Settings → Blacklist    │
└────────────┬──────────────────────────┬──────────────────┘
             │ pilote                   │ écoute (queues)
             ▼                          │
┌────────────────────────────┐          │
│      Moteur d'envoi        │ ─────────┘
│  (thread worker dédié)     │
│   + Selenium + Chrome      │
└────────────┬───────────────┘
             │ persiste
             ▼
┌──────────────────────────────────────────────────────────┐
│           Persistance (hybride SQL + NoSQL)              │
│  SQLite : users, profiles, historique                    │
│  JSON   : config (Settings)                              │
│  TXT    : blacklist                                      │
└──────────────────────────────────────────────────────────┘
```

## 2. Stack technique

| Couche | Technologie | Justification |
|---|---|---|
| Langage | Python 3.11 | Bibliothèque standard riche, écosystème mûr pour Selenium, déploiement multiplateforme |
| GUI | CustomTkinter | Interface moderne au-dessus de `tkinter` (stdlib), look natif sur les trois OS, pas de dépendance lourde type Qt |
| Automatisation Web | Selenium 4 + WebDriver Manager | Pilotage de Chrome, gestion automatique du driver, contournement de l'anti-bot du site cible |
| Base de données | SQLite (module `sqlite3` stdlib) | Mono-fichier, pas de serveur, transactions, contraintes relationnelles |
| Hachage | `bcrypt` | Standard de l'industrie, sel aléatoire intégré, facteur de coût ajustable |
| Configuration | JSON (stdlib `json`) | Lisible, éditable manuellement |
| Liste noire | TXT plat | Liste sans relations, simple à versionner |
| Tests | `pytest`, `pytest-mock` | Framework standard de la communauté Python, fixtures puissantes |
| Packaging | PyInstaller | Exécutable indépendant Windows/macOS/Linux |
| Versionnage | Git + GitHub | Suivi des évolutions, gestion des problèmes |
| Journalisation | `logging` (stdlib) | Multi-niveaux, multi-destinations, rotation possible |

## 3. Architecture en trois couches

```
app/
├── main.py                       Point d'entrée (initialise DB, thème, fenêtre)
├── data/                         Couche persistance
│   ├── database.py               Singleton SQLite, création des tables, requête paramétrée
│   ├── auth_manager.py           Inscription / connexion bcrypt
│   ├── models.py                 Dataclasses (User, UserProfile, Settings, SendingStats)
│   ├── profile_manager.py        CRUD profil utilisateur
│   ├── history_manager.py        Historique des envois (SQL + déduplication)
│   ├── blacklist_manager.py      Liste noire (TXT, NoSQL)
│   └── config_manager.py         Configuration (JSON, NoSQL)
├── core/                         Couche métier
│   ├── sender_engine.py          Moteur d'envoi (thread worker + Selenium)
│   ├── scraper_engine.py         Scraping de l'annuaire pour produire le CSV
│   └── selenium_manager.py       Configuration Chrome, anti-détection, rotation de session
└── ui/                           Couche présentation
    ├── main_window.py            Fenêtre principale (login → dashboard)
    ├── theme.py                  Thème "dark blue", constantes UI
    ├── components/               Composants réutilisables
    │   ├── navigation.py         Barre latérale de navigation
    │   ├── stats_widget.py       Grille de statistiques
    │   └── log_viewer.py         Visionneuse de logs avec filtres
    └── frames/                   Écrans
        ├── login_frame.py
        ├── profile_frame.py
        ├── sending_frame.py
        ├── blacklist_frame.py
        ├── logs_frame.py
        └── settings_frame.py
```

### Principe : séparation stricte

- **`data/`** ne dépend de personne (sauf de la stdlib).
- **`core/`** dépend uniquement de `data/` (et de Selenium pour la partie web).
- **`ui/`** dépend de `core/` et `data/`, jamais l'inverse.

Conséquence pratique : on peut ajouter une nouvelle frame UI sans toucher au moteur d'envoi,
ou réécrire l'UI en CLI sans toucher à la persistance.

## 4. Communication thread-safe entre l'UI et le worker

Tkinter **n'est pas thread-safe** : modifier un widget depuis un thread autre que le main thread
provoque des crashs ou des incohérences visuelles. Le moteur d'envoi tourne dans un thread worker
séparé pour ne pas geler l'interface.

### Modèle de communication

```
┌─────────────────────┐  4 queues thread-safe   ┌───────────────────┐
│       UI            │ ◄─────────────────────  │   Worker thread   │
│  (main thread)      │     - log_queue         │  (SenderEngine)   │
│                     │     - stats_queue       │   + Selenium      │
│  Polling régulier   │     - progress_queue    │                   │
│  toutes les 100ms   │     - company_queue     │                   │
│                     │                         │                   │
│                     │  2 events ─────────────►│                   │
│                     │     - pause_event       │                   │
│                     │     - stop_event        │                   │
└─────────────────────┘                         └───────────────────┘
```

**4 queues sortantes (worker → UI)** : chaque message est un dict typé.
- `log_queue` : `{level, message, time}` pour les logs.
- `stats_queue` : statistiques globales (envoyés, échecs, taux de réussite).
- `progress_queue` : `{current, total}` pour la barre de progression.
- `company_queue` : entreprise en cours, statut, tentative.

**2 events entrants (UI → worker)** : booléens thread-safe.
- `pause_event.set()` met le worker en pause (boucle d'attente).
- `stop_event.set()` arrête proprement la boucle d'envoi.

L'UI lit les queues via un `after(100, ...)` Tkinter (polling), ce qui garantit que toutes les
modifications de widgets se font sur le main thread.

## 5. Choix de stockage — hybride SQL + NoSQL

Le projet illustre deux familles de stockage en choisissant la plus adaptée à chaque besoin.

| Données | Stockage | Justification |
|---|---|---|
| Utilisateurs, profils, historique | **SQLite** (relationnel) | Clés étrangères (`user_id` → users), agrégations SQL (`COUNT`, `SUM CASE WHEN`), contraintes `UNIQUE`, transactions |
| Configuration | **JSON** (NoSQL) | Paires clé/valeur sans relations, lisible, éditable manuellement |
| Liste noire | **TXT** plat (NoSQL) | Liste sans structure, simple à versionner et à partager |

### Schéma SQLite (3 tables)

```
┌─────────────────┐         ┌──────────────────┐
│ users           │         │ profiles         │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │◄────────┤ user_id (FK,UQ)  │
│ username (UQ)   │         │ nom              │
│ password_hash   │         │ prenom           │
│ created_at      │         │ email            │
└─────────────────┘         │ telephone        │
        ▲                   │ objet            │
        │                   │ message          │
        │                   └──────────────────┘
        │
        │                   ┌──────────────────┐
        │                   │ historique       │
        └───────────────────┤ user_id (FK)     │
                            │ url              │
                            │ organisation     │
                            │ statut           │
                            │ tentatives       │
                            │ date_envoi       │
                            └──────────────────┘
```

### Pourquoi `PRAGMA foreign_keys = ON` ?

SQLite désactive les clés étrangères par défaut pour la rétrocompatibilité. On les active à
chaque ouverture de connexion (`database.py`) pour garantir l'intégrité référentielle.

### Pourquoi `check_same_thread=False` ?

Une connexion SQLite est par défaut limitée au thread qui l'a créée. Comme le worker tourne dans
un thread séparé, on autorise le partage. Les requêtes restent sérialisées par SQLite (lock au
niveau du fichier), donc thread-safe en pratique pour ce cas d'usage mono-utilisateur.

## 6. Cycle de vie d'un envoi

1. **Chargement du CSV** : lecture des URLs des organisations.
2. **Filtrage par blacklist** (TXT) : exclusion des organisations à ignorer.
3. **Filtrage par historique** (SQLite) : exclusion des URLs déjà envoyées avec succès.
4. **Initialisation Selenium** : ouverture de Chrome avec configuration anti-détection.
5. **Boucle d'envoi** :
   - Vérification de `stop_event` et `pause_event`.
   - Rotation de session si la durée dépasse le seuil configuré.
   - Remplissage du formulaire (nom, prénom, email, téléphone, objet, message).
   - Attente de la validation anti-bot (timeout configurable).
   - Soumission, vérification du message de confirmation.
   - Enregistrement du résultat dans `historique` (succès ou échec).
   - Mise à jour des statistiques via les queues.
   - Délai aléatoire avant l'envoi suivant (anti-détection).
6. **Finalisation** : fermeture de Chrome, mise à jour des stats finales, signal `DONE` à l'UI.

## 7. Anti-détection Selenium

| Mesure | Implémentation |
|---|---|
| User-agent réel | Chrome récent, profil cohérent |
| Désactivation `navigator.webdriver` | Patch JavaScript à l'ouverture |
| Délai aléatoire entre actions | `time.sleep(random.uniform(min, max))` |
| Rotation de session périodique | Recréation du driver après une durée seuil |
| Mode visible disponible | `--visible` pour le débogage |

## 8. Gestion des erreurs et résilience

- Tout `WebDriverException` ou `TimeoutException` est intercepté et logué.
- En cas de session Chrome invalide, le worker recrée le driver et **retente** la candidature
  jusqu'à `settings.max_tentatives`.
- Erreur HTTP 422 (validation refusée) : retry avec rafraîchissement de la page.
- Toute erreur enregistrée dans l'historique avec le statut `'echec'` : on peut ainsi
  retenter ultérieurement uniquement les échecs (les succès sont protégés par la déduplication).

## 9. Packaging et déploiement

```bash
# Développement
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py

# Production (exécutable autonome)
pip install -r requirements-dev.txt
pyinstaller build.spec
# → dist/FTSender(.exe / .app)
```

`build.spec` configure PyInstaller pour inclure les ressources (icônes, schémas, fichiers
texte par défaut) et générer un binaire indépendant.

## 10. Évolution du projet (maintenance évolutive)

L'historique Git montre les évolutions majeures :

| Phase | Évolution |
|---|---|
| **Février 2025** | Version initiale CLI (`scripts/sender.py`, `scripts/scrapper.py`) |
| **Octobre 2025** | Ajout liste noire, amélioration des logs |
| **Février 2026** | Application desktop CustomTkinter (refonte UI) |
| **Mars 2026** | Authentification, base SQLite, historique de déduplication, tests complets |

Les scripts CLI sont conservés dans `scripts/` comme témoignage de l'évolution et pour les
utilisateurs préférant l'usage en ligne de commande.
