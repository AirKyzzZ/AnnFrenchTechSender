# French Tech Bordeaux - Envoi Automatisé de Candidatures

Script Python pour automatiser l'envoi de candidatures de stage aux entreprises de l'annuaire French Tech Bordeaux.

## 📋 Prérequis

- Python 3.7+
- Google Chrome installé sur votre système
- Connexion internet

## 🚀 Installation

1. Cloner ou télécharger ce répertoire

2. Installer les dépendances Python :
```bash
pip install -r requirements.txt
```

## 📝 Configuration

### 1. Personnaliser votre candidature

Éditez le fichier `sender.py` et modifiez le dictionnaire `CANDIDATURE` avec vos informations :

```python
CANDIDATURE = {
    "nom": "Votre Nom",
    "prenom": "Votre Prénom",
    "email": "votre.email@example.com",
    "telephone": "06 XX XX XX XX",
    "objet": "Candidature pour un stage",
    "message": """Votre message personnalisé..."""
}
```

### 2. Liste noire des organisations

Le fichier `blacklist.txt` contient les URLs des organisations à ignorer (déjà contactées ou ayant répondu).

Format : une URL par ligne
```
https://annuaire.frenchtechbordeaux.com/organisations/nom-organisation
```

Ajoutez simplement les URLs des organisations que vous souhaitez exclure.

#### Gestionnaire de liste noire

Un script utilitaire est fourni pour gérer facilement la liste noire :

```bash
# Afficher la liste noire
python blacklist_manager.py list

# Ajouter une organisation
python blacklist_manager.py add https://annuaire.frenchtechbordeaux.com/organisations/nom-entreprise

# Retirer une organisation
python blacklist_manager.py remove https://annuaire.frenchtechbordeaux.com/organisations/nom-entreprise

# Afficher l'aide
python blacklist_manager.py help
```

## 🔧 Utilisation

### Étape 1 : Récupérer les URLs des entreprises

Exécutez le script de scraping pour récupérer toutes les URLs de l'annuaire :

```bash
python scrapper.py
```

Ce script va :
- Parcourir toutes les pages de l'annuaire French Tech Bordeaux
- Extraire les URLs de toutes les organisations
- Générer le fichier `urls_entreprises.csv`
- Créer un fichier de logs `scrapper_logs.log`

**Durée estimée** : ~10-15 minutes pour 151 pages

### Étape 2 : Tester l'envoi (mode test)

**RECOMMANDÉ** : Avant d'envoyer réellement, testez d'abord en mode simulation :

```bash
python sender.py --dry-run
# ou
python sender.py --test
```

Ce mode va :
- Charger la liste noire et filtrer les organisations
- Simuler l'envoi sans réellement envoyer les candidatures
- Vous montrer combien de candidatures seraient envoyées
- Créer des logs de test

### Étape 3 : Envoyer les candidatures

Une fois satisfait du test, lancez l'envoi réel :

```bash
python sender.py
```

Ce script va :
- Charger la liste noire depuis `blacklist.txt`
- Filtrer les organisations à contacter
- Envoyer automatiquement les candidatures
- Créer un fichier de logs `candidature_logs.log`

**⚠️ ATTENTION** : Le script envoie réellement les emails ! Vérifiez bien votre configuration avant de lancer.

## 📊 Fichiers du projet

### Fichiers de configuration
- `blacklist.txt` : Liste noire des organisations à ignorer (éditable manuellement)
- `requirements.txt` : Dépendances Python du projet

### Fichiers générés
- `urls_entreprises.csv` : Liste des URLs des organisations scrapées
- `candidature_logs.log` : Logs détaillés des candidatures envoyées
- `scrapper_logs.log` : Logs du processus de scraping

### Scripts
- `scrapper.py` : Script de récupération des URLs
- `sender.py` : Script d'envoi des candidatures
- `blacklist_manager.py` : Utilitaire de gestion de la liste noire

## 🛡️ Sécurité et bonnes pratiques

1. **Ne commitez jamais vos informations personnelles** dans un dépôt public
2. Respectez un délai de 5 secondes entre chaque envoi (déjà configuré)
3. Vérifiez régulièrement les logs pour détecter d'éventuelles erreurs
4. Mettez à jour la liste noire après chaque campagne

## 🔍 Dépannage

### Problème : ChromeDriver ne fonctionne pas
**Solution** : Le script utilise `webdriver-manager` qui télécharge automatiquement la bonne version de ChromeDriver. Assurez-vous que Chrome est installé.

### Problème : Trop d'erreurs lors du scraping
**Solution** : Vérifiez votre connexion internet. Le script s'arrête automatiquement après 10 erreurs consécutives.

### Problème : Les formulaires ne se remplissent pas
**Solution** : Le site web a peut-être changé sa structure HTML. Vous devrez peut-être mettre à jour les sélecteurs CSS dans `sender.py`.

## 📅 Historique des versions

- **Octobre 2025** : Ajout de la liste noire, amélioration des logs, mise à jour pour 2026
- **Février 2025** : Version initiale

## ⚖️ Licence et responsabilité

Ce script est fourni à des fins éducatives. L'utilisateur est seul responsable de son utilisation. Assurez-vous de respecter les conditions d'utilisation du site French Tech Bordeaux.

## 📧 Contact

Maxime Mansiet - maxime.mansiet@gmail.com

