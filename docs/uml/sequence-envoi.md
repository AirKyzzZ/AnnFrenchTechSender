# Diagramme de séquence — Envoi automatisé d'une candidature

```mermaid
sequenceDiagram
    autonumber
    actor U as Utilisateur
    participant SF as SendingFrame (UI)
    participant SE as SenderEngine (worker)
    participant SM as SeleniumManager
    participant CR as Chrome (driver)
    participant HM as HistoryManager
    participant DB as SQLite

    U->>SF: clique « Démarrer l'envoi »
    SF->>SE: start(profile, settings, history_manager)
    SE->>SE: lance thread worker (daemon=True)

    rect rgb(245, 245, 250)
    Note over SE: dans le thread worker
    SE->>HM: get_urls_envoyees()
    HM->>DB: SELECT url FROM historique<br/>WHERE statut='succes' AND user_id=?
    DB-->>HM: set d'URLs déjà traitées
    HM-->>SE: set d'URLs

    SE->>SE: filtrer CSV (blacklist + historique)
    SE->>SM: initialiser_driver()
    SM->>CR: lancer Chrome avec config anti-détection
    CR-->>SM: driver
    SM-->>SE: driver

    loop pour chaque URL non déjà envoyée
        SE->>SE: vérifier stop_event / pause_event
        SE->>CR: get(url)
        SE->>CR: find_element + send_keys (formulaire)
        SE->>CR: attendre bouton anti-bot prêt
        SE->>CR: submit_button.click()
        SE->>CR: vérifier message de confirmation

        alt envoi réussi
            SE->>HM: enregistrer_envoi(url, 'succes')
            HM->>DB: INSERT INTO historique (...)
            DB-->>HM: OK
            SE->>SF: stats_queue.put({+1 succès})
        else timeout / échec
            SE->>HM: enregistrer_envoi(url, 'echec')
            SE->>SF: stats_queue.put({+1 échec})
        end

        SE->>SE: time.sleep(delay aléatoire)
    end

    SE->>SM: fermer()
    SM->>CR: driver.quit()
    SE->>SF: log_queue.put("DONE")
    end

    SF->>U: affiche "Envoi terminé"
```

## Notes

- **Étape 9** : les URLs déjà envoyées avec succès sont **filtrées en amont** — preuve de la
  déduplication (compétence « Gérer les données »).
- **Étapes 11-12** : la configuration anti-détection est appliquée à chaque ouverture de
  driver.
- **Étapes répétées** : la boucle vérifie `stop_event` à chaque itération pour permettre un
  arrêt propre (compétence « Concevoir et développer » : robustesse).
- **Étape 30 (DONE)** : signal de fin que l'UI utilise pour réactiver le bouton « Démarrer ».
