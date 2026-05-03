# Diagramme de classes, FT Sender

```mermaid
classDiagram
    class Database {
        -conn: sqlite3.Connection
        -db_path: str
        +executer(requete, params) Cursor
        +commit()
        +fermer()
        -_creer_tables()
    }

    class AuthManager {
        -db: Database
        +inscrire(username, password) tuple
        +connecter(username, password) tuple
        +utilisateur_existe(username) bool
        +get_username(user_id) str
    }

    class ProfileManager {
        -db: Database
        -user_id: int
        +sauvegarder(profile)
        +charger() UserProfile
    }

    class HistoryManager {
        -db: Database
        -user_id: int
        +enregistrer_envoi(url, statut, tentatives)
        +deja_envoye(url) bool
        +get_urls_envoyees() set
        +get_historique(limite) list
        +compter_envois() dict
    }

    class BlacklistManager {
        -filepath: str
        +load() list
        +save(urls)
        +add(url) bool
        +remove(url) bool
        +contains(url) bool
        +as_set() set
    }

    class ConfigManager {
        -config_path: str
        +save(settings)
        +load() Settings
    }

    class SenderEngine {
        -log_queue: Queue
        -stats_queue: Queue
        -progress_queue: Queue
        -company_queue: Queue
        -pause_event: Event
        -stop_event: Event
        -_thread: Thread
        -_selenium: SeleniumManager
        -_stats: SendingStats
        +start(profile, settings, history_manager, dry_run)
        +pause()
        +resume()
        +stop()
        -_run(...)
        -_envoyer_candidature(url, ...)
        -_finalize()
    }

    class SeleniumManager {
        -settings: Settings
        -driver: WebDriver
        +initialiser_driver()
        +get_driver() WebDriver
        +session_expiree() bool
        +relancer_session(raison)
        +fermer()
    }

    class User {
        +id: int
        +username: str
    }
    class UserProfile {
        +nom: str
        +prenom: str
        +email: str
        +telephone: str
        +objet: str
        +message: str
        +to_dict() dict
        +from_dict(data) UserProfile
        +is_valid() bool
    }
    class Settings {
        +delay_min: float
        +delay_max: float
        +timeout_page: int
        +timeout_bouton: int
        +max_tentatives: int
        +headless: bool
        +csv_path: str
        +blacklist_path: str
        +to_dict() dict
        +from_dict(data) Settings
    }
    class SendingStats {
        +total: int
        +envoyes: int
        +echecs: int
        +taux_reussite: float
        +traites: int
        +to_dict() dict
    }

    AuthManager       --> Database
    ProfileManager    --> Database
    HistoryManager    --> Database
    SenderEngine      --> SeleniumManager
    SenderEngine      ..> HistoryManager : utilise
    SenderEngine      ..> BlacklistManager : utilise
    SenderEngine      ..> UserProfile : utilise
    SenderEngine      ..> Settings : utilise
    SenderEngine      ..> SendingStats : agrège
    ConfigManager     ..> Settings : sérialise
    ProfileManager    ..> UserProfile : sérialise
```

## Légende

- `→` association (composition / référence forte)
- `..>` dépendance (utilisation transitoire)

## Observations

- **Une seule instance de `Database`** est partagée par tous les managers SQL → cohérence
  transactionnelle.
- **`SenderEngine` ne dépend pas directement de la base** : il reçoit un `HistoryManager`
  injecté → testable avec un mock.
- **`Settings` et `UserProfile` sont des `@dataclass`** → typage statique, sérialisation
  automatique, valeurs par défaut explicites.
