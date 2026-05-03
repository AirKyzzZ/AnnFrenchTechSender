# Sécurité, FT Sender

> Synthèse des mesures de sécurité du projet, pour l'épreuve E6 BTS SIO SLAM.

## 1. Injection SQL

**Risque.** Concaténer des entrées utilisateur dans une requête SQL permet à un attaquant
d'exécuter du SQL arbitraire (`' OR 1=1 --`).

**Mesure.** Toutes les requêtes utilisent des **paramètres préparés** (placeholder `?`).
La méthode `Database.executer()` impose ce contrat.

```python
# DANGEREUX (jamais utilisé dans le projet) :
cur.execute(f"SELECT * FROM users WHERE username = '{nom}'")

# SÉCURISÉ (pratique systématique) :
cur.execute("SELECT * FROM users WHERE username = ?", (nom,))
```

**Vérification.** Une recherche `grep -r 'execute.*f"' app/` ne renvoie aucun résultat
problématique : aucune f-string n'est utilisée pour construire du SQL.

## 2. Hachage des mots de passe

**Risque.** Stocker les mots de passe en clair (ou hachés en MD5/SHA1) expose tous les comptes
en cas de fuite de la base.

**Mesure.** `bcrypt` avec un sel aléatoire automatique et un facteur de coût de 12 rounds
(par défaut). Voir [`auth_manager.py`](../app/data/auth_manager.py) :

```python
password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
# ...
if bcrypt.checkpw(password.encode("utf-8"), hash_stocke):
    return True
```

**Pourquoi bcrypt ?**
- Sel aléatoire intégré → résiste aux **rainbow tables**.
- Facteur de coût ajustable → résiste à l'évolution de la puissance de calcul.
- Comparaison `checkpw()` en **temps constant** → résiste aux attaques par chronométrage.
- Standard de l'industrie (recommandé par OWASP).

## 3. Messages d'erreur génériques

**Risque.** Distinguer « utilisateur inexistant » de « mot de passe incorrect » permet à un
attaquant d'énumérer les comptes valides.

**Mesure.** Un seul message générique : « Nom d'utilisateur ou mot de passe incorrect »
(cf. `AuthManager.connecter()`).

## 4. Isolation par utilisateur

**Risque.** Sans isolation, un utilisateur authentifié pourrait lire les données des autres
en falsifiant un identifiant.

**Mesure.** Toutes les lectures filtrent strictement par `user_id` :

```sql
SELECT ... FROM historique  WHERE user_id = ? ...
SELECT ... FROM profiles    WHERE user_id = ? ...
```

L'`user_id` provient de la session courante (validée par `bcrypt.checkpw()`) et n'est jamais
issu d'une entrée utilisateur directe.

## 5. Anti-détection Selenium

**Risque.** Le site cible peut bloquer ou ralentir les bots automatisés.

**Mesures.** Voir [`selenium_manager.py`](../app/core/selenium_manager.py) :

- Désactivation de `navigator.webdriver` (patch JS injecté à l'ouverture).
- User-agent réel et cohérent.
- Délais aléatoires entre les actions humaines (`time.sleep(random.uniform(min, max))`).
- Rotation périodique de session Chrome (`relancer_session()`) pour éviter les sessions
  trop longues.

⚠️ **Important.** Ces mesures relèvent de la **résilience technique**, pas du contournement
d'une protection légale. L'utilisateur reste responsable du respect des conditions
d'utilisation du site cible.

## 6. Données sensibles côté disque

| Donnée | Localisation | Sensibilité |
|---|---|---|
| Mots de passe utilisateurs | `data/ftsender.db` (table `users`) | **Hachés** bcrypt, jamais en clair |
| Profils (nom, email, téléphone) | `data/ftsender.db` (table `profiles`) | Données personnelles **locales** |
| Historique des envois | `data/ftsender.db` (table `historique`) | Métadonnées (URL, date, statut) |
| Configuration | `data/config.json` | Pas de secret |
| Liste noire | `blacklist.txt` | Liste publique du domaine |
| Logs | `*.log` | Peuvent contenir des URLs ; à ne pas commiter (cf. `.gitignore`) |

**Le fichier `.env`** contient les paramètres environnementaux (chemins, mode debug). Il est
listé dans `.gitignore` et **non versionné**.

## 7. Modèle de menace

| Menace | Couverte ? | Notes |
|---|---|---|
| Vol du fichier `.db` | Partielle | Mots de passe hachés ; profils accessibles si l'attaquant a le fichier |
| Attaquant local sur la machine | Hors scope | Application desktop : si l'OS est compromis, tout l'est |
| Injection SQL | Couverte | Requêtes paramétrées partout |
| Brute-force sur mot de passe | Couverte | bcrypt 12 rounds = ralenti significativement |
| Énumération de comptes | Couverte | Messages d'erreur génériques |
| Détection bot par site cible | Mitigée | Anti-détection Selenium + délais aléatoires |
| Capture des saisies utilisateur | Hors scope | Keylogger système : protection OS |

## 8. Recommandations pour un déploiement multi-utilisateurs

(Hors scope du projet actuel, mais à mentionner si le jury demande.)

- Chiffrer la base SQLite avec **SQLCipher** ou pcrypt-sqlite.
- Ajouter un **2FA** par TOTP (`pyotp`).
- Limiter les tentatives de login (anti brute-force).
- Migrer vers une base PostgreSQL avec rôles dédiés.
