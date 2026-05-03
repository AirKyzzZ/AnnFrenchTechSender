# Diagramme de séquence — Authentification (login)

```mermaid
sequenceDiagram
    autonumber
    actor U as Utilisateur
    participant LF as LoginFrame
    participant AM as AuthManager
    participant DB as Database (SQLite)
    participant BC as bcrypt

    U->>LF: saisit (username, password)
    LF->>AM: connecter(username, password)
    AM->>AM: validation longueur / non-vide
    AM->>DB: SELECT id, password_hash<br/>FROM users WHERE username = ?
    DB-->>AM: row { id, password_hash } ou None

    alt utilisateur inexistant
        AM-->>LF: (False, None, "incorrect")
        LF-->>U: message d'erreur générique
    else utilisateur trouvé
        AM->>BC: checkpw(password, hash_stocke)
        alt mot de passe correct
            BC-->>AM: True
            AM-->>LF: (True, user_id, "OK")
            LF->>LF: passer au dashboard<br/>(MainWindow)
        else mot de passe incorrect
            BC-->>AM: False
            AM-->>LF: (False, None, "incorrect")
            LF-->>U: message d'erreur générique
        end
    end
```

## Notes de sécurité

- **Étape 4** : la requête utilise un paramètre préparé (`?`), pas de concaténation.
- **Étape 6** : `bcrypt.checkpw()` est en temps constant (résiste aux attaques par chronométrage).
- **Message d'erreur** : volontairement identique pour « utilisateur inexistant » et
  « mot de passe incorrect » → empêche l'énumération de comptes.
- **Aucun mot de passe en clair** ne transite ni dans les logs ni en base.
