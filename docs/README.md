# Documentation FT Sender, dossier BTS SIO E6

> Documentation technique du projet **AnnFrenchTechSender** (FT Sender), réalisation
> professionnelle n° 2 du dossier de l'épreuve E6 du BTS SIO option SLAM, session 2026.

## Sommaire

| Document | Contenu |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Stack technique, architecture en trois couches, threading, communication thread-safe, choix de stockage |
| [`COMPETENCES.md`](COMPETENCES.md) | Mapping détaillé des trois compétences SLAM (Concevoir+dev, Maintenance, Gérer les données) avec preuves de code |
| [`SECURITE.md`](SECURITE.md) | Hachage bcrypt, requêtes paramétrées, anti-détection Selenium, isolation par utilisateur |
| [`TESTS.md`](TESTS.md) | Stratégie de tests (unitaires, intégration, E2E), couverture, commandes |
| [`uml/`](uml/) | Diagrammes Mermaid : cas d'utilisation, séquences, classes, déploiement, MCD |

## Parcours suggéré pour le jury

1. Lire le **[README principal](../README.md)** pour la vision produit (5 min).
2. Survoler l'**[architecture](ARCHITECTURE.md)** pour comprendre la séparation des responsabilités (5 min).
3. Consulter le **[mapping des compétences](COMPETENCES.md)** pour les preuves bloc 2 SLAM (10 min).
4. Vérifier la **[sécurité](SECURITE.md)** et les **[tests](TESTS.md)** (5 min chacun).
5. Naviguer les **[diagrammes UML](uml/)** selon les questions précises.

## Liens externes

- **Code source** : <https://github.com/AirKyzzZ/AnnFrenchTechSender>
- **Suivi des problèmes** : <https://github.com/AirKyzzZ/AnnFrenchTechSender/issues>
- **CI** : <https://github.com/AirKyzzZ/AnnFrenchTechSender/actions>
- **Auteur** : Maxime Mansiet, <https://maximemansiet.fr>
