# Compétences SLAM — FT Sender

> Mapping détaillé des trois compétences du bloc 2 SLAM (BTS SIO 2026) avec
> liens directs vers le code source.

## Compétence 1 — Concevoir et développer une solution applicative

### Sous-compétence : Analyser un besoin exprimé et son contexte juridique

- **Besoin** documenté dans le [`README.md`](../README.md#fonctionnalites) : automatisation
  d'envois de candidatures avec déduplication et anti-détection.
- **Contexte juridique** : le projet est destiné à un usage **personnel** ; l'utilisateur est
  responsable du respect des conditions d'utilisation du site cible. Les données collectées
  (profil, historique) sont **strictement locales**, ce qui évite toute problématique RGPD côté
  tiers.

### Sous-compétence : Participer à la conception de l'architecture

- Architecture en **trois couches** : `data/`, `core/`, `ui/` — voir
  [`ARCHITECTURE.md`](ARCHITECTURE.md#3-architecture-en-trois-couches).
- Diagramme de composants Mermaid : [`uml/classes.md`](uml/classes.md).

### Sous-compétence : Modéliser une solution applicative

- **Modèles métier** : `app/data/models.py` utilise des `@dataclass` typées pour
  `User`, `UserProfile`, `Settings`, `SendingStats`.
- **Modèle de données** relationnel : voir [`uml/mcd.md`](uml/mcd.md).
- **Diagrammes de séquence** :
  - [`uml/sequence-auth.md`](uml/sequence-auth.md) — login bcrypt
  - [`uml/sequence-envoi.md`](uml/sequence-envoi.md) — envoi automatisé

### Sous-compétence : Exploiter les ressources du cadre applicatif (framework)

- **CustomTkinter** comme framework UI au-dessus de `tkinter` (stdlib).
- **Selenium WebDriver** comme framework d'automatisation.
- Patterns appliqués : Singleton (Database), Worker thread, Producer/Consumer (queues),
  Strategy (manager spécialisé par type de stockage).

### Sous-compétence : Identifier, développer, utiliser ou adapter des composants logiciels

- Composants UI réutilisables dans `app/ui/components/` :
  - [`navigation.py`](../app/ui/components/navigation.py) — barre latérale
  - [`stats_widget.py`](../app/ui/components/stats_widget.py) — grille de stats
  - [`log_viewer.py`](../app/ui/components/log_viewer.py) — visionneuse filtrée
- **Adaptation** : `WebDriver Manager` pour gérer automatiquement la version du driver Chrome.

### Sous-compétence : Utiliser des composants d'accès aux données

- Toutes les opérations SQL passent par `Database.executer()`
  ([`database.py`](../app/data/database.py)) avec **requêtes paramétrées** (anti-injection).
- Managers spécialisés : `AuthManager`, `ProfileManager`, `HistoryManager`.

### Sous-compétence : Intégrer en continu les versions

- **Git/GitHub** : commits structurés, branches de fonctionnalités fusionnées sur `main`.
- Repository public : <https://github.com/AirKyzzZ/AnnFrenchTechSender>.

### Sous-compétence : Réaliser les tests

- Voir [`TESTS.md`](TESTS.md).
- Trois niveaux : unitaires, intégration, end-to-end (avec mocks Selenium).

### Sous-compétence : Rédiger des documentations technique et d'utilisation

- **Documentation utilisateur** : [`README.md`](../README.md) (installation, première utilisation, captures).
- **Documentation technique** : ce dossier `docs/` (architecture, compétences, sécurité, tests, UML).
- **Code commenté en français** : chaque module a un docstring explicatif et des commentaires
  pédagogiques sur les choix techniques (cf. `database.py`, `auth_manager.py`, etc.).

### Sous-compétence : Exploiter les fonctionnalités d'un environnement de développement et de tests

- IDE : VS Code avec extensions Python, Pylance, GitLens.
- Tests : `pytest` avec fixtures partagées dans `tests/conftest.py`.
- Debugging : logs structurés (`candidature_logs.log`, `scrapper_logs.log`).

---

## Compétence 2 — Assurer la maintenance corrective ou évolutive

### Sous-compétence : Recueillir, analyser et mettre à jour les informations sur une version

- **Historique Git détaillé** retraçant les évolutions :
  - Phase CLI initiale : `scripts/sender.py`, `scripts/scrapper.py`
  - Phase desktop : ajout du dossier `app/`, refonte avec UI CustomTkinter
  - Phase données : migration profils JSON → SQLite, ajout `users` + `historique`
  - Phase robustesse : anti-détection, rotation de session, tests automatisés
- **Suivi des problèmes** : GitHub Issues.

### Sous-compétence : Évaluer la qualité d'une solution applicative

- **Métriques** :
  - 30+ tests automatisés (unitaires + intégration + E2E)
  - Logs structurés permettent l'analyse post-mortem
  - Couverture des cas d'erreur (timeout, session invalide, formulaire HTTP 422)

### Sous-compétence : Analyser et corriger un dysfonctionnement

Exemples concrets dans l'historique :

- **Refresh de la page après timeout du bouton anti-bot** (`sender_engine.py` : retry avec
  `driver.refresh()`).
- **Session Chrome invalide** détectée (`"invalid session"` dans `WebDriverException`) →
  réinitialisation automatique du driver + retry de la candidature en cours.
- **Évitement des doublons après redémarrage** : avant la phase « historique SQLite »,
  l'application reprenait toutes les organisations à zéro à chaque lancement. Correction
  via `HistoryManager.deja_envoye()` qui vérifie en SQL avant chaque envoi.

### Sous-compétence : Mettre à jour des documentations technique et d'utilisation

- README régénéré à chaque grande évolution (cf. git log).
- Ce dossier `docs/` reflète l'état actuel du code.

### Sous-compétence : Élaborer et réaliser les tests des éléments mis à jour

- Voir [`TESTS.md`](TESTS.md). À chaque évolution majeure, des tests dédiés sont ajoutés
  (`test_auth.py` ajouté avec l'authentification ; `test_history.py` ajouté avec la
  déduplication).

---

## Compétence 3 — Gérer les données

### Sous-compétence : Exploiter des données à l'aide d'un langage de requêtes

Exemples de requêtes SQL utilisées :

```sql
-- Authentification (database.py via auth_manager.py)
SELECT id, password_hash FROM users WHERE username = ?

-- Déduplication (history_manager.py)
SELECT id FROM historique
WHERE user_id = ? AND url = ? AND statut = 'succes'

-- Statistiques agrégées (history_manager.py)
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN statut = 'succes' THEN 1 ELSE 0 END) AS succes,
  SUM(CASE WHEN statut = 'echec'  THEN 1 ELSE 0 END) AS echecs
FROM historique
WHERE user_id = ?
```

Toutes les requêtes utilisent des **paramètres préparés** (`?`), jamais de concaténation
de chaînes — voir [`SECURITE.md`](SECURITE.md#1-injection-sql).

### Sous-compétence : Développer des fonctionnalités applicatives au sein d'un SGBD

- Création des tables avec contraintes (`PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `NOT NULL`,
  `DEFAULT`) — voir [`database.py`](../app/data/database.py).
- Activation des clés étrangères : `PRAGMA foreign_keys = ON`.

### Sous-compétence : Concevoir ou adapter une base de données

- **Modèle relationnel** : 3 tables avec dépendances (users → profiles, users → historique).
- **Adaptation** : la première version stockait les profils dans des fichiers JSON par utilisateur ;
  migration vers SQLite quand l'authentification a été introduite (cohérence transactionnelle
  + jointures avec l'historique).

### Sous-compétence : Administrer et déployer une base de données

- **Création automatique** des tables au premier lancement (`Database._creer_tables()`).
- **Sauvegarde** : copie simple du fichier `data/ftsender.db` (mono-fichier).
- **Restauration** : remettre le fichier copié à sa place.
- **Habilitations** : chaque utilisateur ne voit que ses propres données via filtre
  `WHERE user_id = ?` dans toutes les lectures.

---

## Choix de stockage justifié (point fort pour l'oral)

Le projet utilise volontairement **trois types de stockage** complémentaires :

| Type | Stockage | Pourquoi ce choix |
|---|---|---|
| Relationnel | SQLite | Données avec relations (user_id), agrégations SQL, transactions, contraintes |
| NoSQL document | JSON | Configuration : paires clé/valeur sans relations, lisible humainement |
| NoSQL clé-valeur | TXT (lignes) | Liste plate, simple à versionner, éditable manuellement |

Cette **hybridation justifiée** est précisément ce que la grille d'évaluation E6 SLAM
(Annexe VII-5-B) demande au critère « Le choix du type de base de données est pertinent ».
