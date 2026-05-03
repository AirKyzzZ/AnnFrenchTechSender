# Diagramme de cas d'utilisation, FT Sender

```mermaid
flowchart TB
    subgraph "FT Sender"
        UC1["Créer un compte<br/>(inscription bcrypt)"]
        UC2["Se connecter"]
        UC3["Renseigner son profil<br/>de candidature"]
        UC4["Configurer les paramètres<br/>(délais, timeouts)"]
        UC5["Démarrer un envoi"]
        UC6["Mettre en pause / reprendre"]
        UC7["Arrêter un envoi"]
        UC8["Consulter les logs"]
        UC9["Gérer la liste noire"]
        UC10["Consulter l'historique<br/>et les statistiques"]
        UC11["Scraper l'annuaire<br/>(génération CSV)"]
    end

    Utilisateur((Utilisateur))
    Site["Site French Tech Bordeaux<br/>(formulaires de contact)"]

    Utilisateur --> UC1
    Utilisateur --> UC2
    Utilisateur --> UC3
    Utilisateur --> UC4
    Utilisateur --> UC5
    Utilisateur --> UC6
    Utilisateur --> UC7
    Utilisateur --> UC8
    Utilisateur --> UC9
    Utilisateur --> UC10
    Utilisateur --> UC11

    UC5 -.envoie via Selenium.-> Site
    UC11 -.scrape.-> Site

    UC2 -.requiert.-> UC1
    UC5 -.requiert.-> UC2
    UC5 -.requiert.-> UC3
```

## Acteurs

- **Utilisateur** : un seul utilisateur authentifié à la fois (mono-utilisateur par session).
  Plusieurs utilisateurs peuvent coexister dans la base ; chacun ne voit que ses propres
  données (filtrage `WHERE user_id = ?`).
- **Site French Tech Bordeaux** (acteur secondaire) : la cible de l'automatisation
  Selenium.

## Cas d'utilisation prioritaires

1. **UC5, Démarrer un envoi** : cas central. Démarre le worker, charge les URLs, filtre par
   blacklist + historique, lance la boucle Selenium, met à jour les stats en temps réel.
2. **UC10, Consulter l'historique** : montre la valeur du choix de stockage relationnel
   (agrégations SQL).
3. **UC11, Scraper l'annuaire** : génère le fichier CSV des organisations à contacter.
