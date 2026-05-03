# Tests, FT Sender

> Stratégie de tests automatisés, pour l'épreuve E6 BTS SIO SLAM.

## 1. Pyramide de tests

```
                ╱─────────────╲
               ╱  E2E (1 fich.)╲      ← test_e2e.py, envoi simulé avec mocks Selenium
              ╱─────────────────╲
             ╱  Intégration (1)  ╲    ← test_integration.py, parcours auth → profil → historique
            ╱─────────────────────╲
           ╱   Unitaires (6 fich.) ╲  ← models, database, auth, blacklist, config, history
          ╱─────────────────────────╲
```

## 2. Outils

- **`pytest`** : framework de tests Python (le plus utilisé de l'écosystème).
- **`pytest-mock`** : facilités de mocking, notamment pour Selenium.
- **`tempfile`** : bases de données temporaires pour les tests d'intégration.
- **Fixtures** partagées dans `tests/conftest.py` (par exemple `db_temp`, `user_temp`).

## 3. Tests unitaires

| Fichier | Cible | Vérifications principales |
|---|---|---|
| `test_models.py` | `dataclass` métier | sérialisation `to_dict()` / `from_dict()`, validations métier, valeurs par défaut |
| `test_database.py` | `Database` | création des tables, requêtes paramétrées, transactions, contraintes FK |
| `test_auth.py` | `AuthManager` | inscription nouveau, doublon refusé, mot de passe trop court, login OK / KO, message d'erreur générique |
| `test_blacklist.py` | `BlacklistManager` | load/save, dédoublonnage, ordre alphabétique, lignes commentées ignorées |
| `test_config.py` | `ConfigManager` | sauvegarde JSON pretty, chargement par défaut si fichier absent |
| `test_history.py` | `HistoryManager` | enregistrement, déduplication par `(url, statut)`, statistiques agrégées |

## 4. Tests d'intégration

`test_integration.py` valide le **parcours complet** sur une base de données éphémère :

1. Inscription d'un utilisateur via `AuthManager`.
2. Connexion → récupération de l'`user_id`.
3. Création d'un profil via `ProfileManager`.
4. Enregistrement de plusieurs envois via `HistoryManager`.
5. Vérification que les statistiques agrégées sont cohérentes.
6. Vérification que la déduplication fonctionne (un second appel à `enregistrer_envoi`
   sur la même URL avec statut `'succes'` est ignoré par `deja_envoye()`).

## 5. Tests end-to-end

`test_e2e.py` simule un envoi complet **sans ouvrir Chrome** :

- `SenderEngine` est instancié avec un `SeleniumManager` **mocké**.
- Les méthodes `driver.find_element`, `driver.get`, etc. sont remplacées par des mocks
  programmés pour simuler succès/échec/timeout.
- On vérifie :
  - que les queues reçoivent les messages attendus (logs, stats, progress, company),
  - que les events `pause` et `stop` sont respectés,
  - que les résultats sont persistés dans `historique`.

## 6. Couverture des comportements anormaux (exigence Annexe II.E)

- **Timeout du bouton anti-bot** → retry avec rafraîchissement.
- **Session Chrome invalide** → réinitialisation du driver + retry.
- **Erreur HTTP 422** → retry simulé.
- **Stop pendant un envoi** → arrêt propre, log explicite.
- **CSV introuvable** → message d'erreur explicite, pas de crash.

## 7. Commandes

```bash
# Installer les dépendances de développement
pip install -r requirements-dev.txt

# Lancer tous les tests
python -m pytest tests/ -v

# Tests unitaires uniquement
python -m pytest tests/test_models.py tests/test_database.py \
                 tests/test_auth.py tests/test_blacklist.py \
                 tests/test_config.py tests/test_history.py -v

# Tests d'intégration
python -m pytest tests/test_integration.py -v

# Tests end-to-end
python -m pytest tests/test_e2e.py -v

# Couverture
pip install pytest-cov
python -m pytest tests/ --cov=app --cov-report=html
# ouvrir htmlcov/index.html
```

## 8. Tests de non-régression

À chaque grande évolution (cf. historique git), les tests unitaires existants étaient
exécutés avant le merge sur `main`. Aucun ajout de fonctionnalité n'a été mergé sans que
les tests passent.

L'ajout de nouvelles fonctionnalités s'est fait **avec ses propres tests** :

- Ajout de `HistoryManager` → ajout de `test_history.py` (8 tests).
- Ajout de `AuthManager` → ajout de `test_auth.py` (10 tests).
- Ajout de `BlacklistManager` → ajout de `test_blacklist.py` (6 tests).

## 9. Limites actuelles et améliorations possibles

- Tests Selenium réels (sans mocks) : non automatisés car nécessitent un site cible stable.
- Couverture de la couche UI Tkinter : non testée automatiquement (nécessiterait `pytest-qt`
  ou similaire pour driver l'interface).
- CI GitHub Actions : à brancher pour exécuter `pytest` sur chaque push.
