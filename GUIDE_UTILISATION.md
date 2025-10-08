# 📧 Guide d'utilisation - French Tech Bordeaux Sender

## 🔍 Problème résolu

### Symptôme initial
Le script fonctionnait uniquement sur les 2-3 premières entreprises, puis plus aucune confirmation par email pour les suivantes.

### Cause identifiée
1. **Pas de vérification de confirmation** : Le script soumettait le formulaire et supposait le succès, mais ne vérifiait pas si le message "Votre message a bien été envoyé" apparaissait réellement
2. **Soumission non naturelle** : Utilisation de `form.submit()` qui peut être bloquée comme comportement de bot
3. **Sessions trop longues** : Le driver Selenium gardait la même session trop longtemps, devenant suspect pour le serveur
4. **Erreurs 422 silencieuses** : Le serveur rejetait les soumissions mais le script ne le détectait pas

## ✅ Corrections apportées

### 1. **Vérification du message de confirmation** ⭐ CLEF DU FIX
Le script attend maintenant explicitement l'apparition du message "Votre message a bien été envoyé !" avant de marquer un envoi comme réussi.

```python
# Attend le message de confirmation (max 15 secondes)
confirmation = wait.until(
    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Votre message a bien été envoyé')]"))
)
```

### 2. **Clic sur le bouton au lieu de form.submit()**
Simulation d'un vrai utilisateur en cliquant sur le bouton submit :

```python
submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
submit_button.click()  # Plus naturel que form.submit()
```

### 3. **Renouvellement de session**
Le driver Chrome est recréé automatiquement tous les 20 envois pour éviter les sessions suspectes.

### 4. **Gestion de la pop-up cookies**
Acceptation automatique de la pop-up cookies qui pouvait bloquer l'interaction avec le formulaire.

### 5. **Détection des erreurs 422**
Le script détecte maintenant quand le serveur rejette une soumission (erreur 422) et le log clairement.

### 6. **Délai augmenté**
Pause de 8 secondes entre chaque envoi (au lieu de 5) pour éviter le rate limiting.

## 🚀 Comment utiliser

### Étape 1 : Test de validation (RECOMMANDÉ)
```bash
python test_final.py
```
Ce script :
- Teste l'envoi sur 3 entreprises
- Utilise des infos de TEST (pas vos vraies données)
- Valide que tout fonctionne

**Si ce test réussit à 100%, passez à l'étape 2 !**

### Étape 2 : Mode test complet (simulation sans envoi)
```bash
python sender.py --dry-run
```
Simule l'envoi sur toutes les entreprises sans rien envoyer réellement.

### Étape 3 : Envoi réel
```bash
python sender.py
```
Lance l'envoi réel sur toutes les entreprises.

**⚠️ IMPORTANT** : Le script va prendre plusieurs heures (2217 entreprises × 8 secondes = ~5 heures)

## 📊 Suivi en temps réel

Le script affiche :
- Progression en temps réel `[15/2217]`
- Succès/échecs pour chaque envoi
- Statistiques tous les 10 envois
- Rapport final avec taux de réussite

Exemple de sortie :
```
[10/2217] Envoi en cours...
✓ Candidature envoyée avec succès à https://...

--- Statistiques intermédiaires ---
Succès: 9 | Échecs: 1 | Total traité: 10/2217
Taux de réussite: 90.0%
```

## 📁 Fichiers générés

### `candidature_logs.log`
Logs détaillés de tous les envois avec horodatage. Utile pour déboguer.

### `echecs_candidatures.txt`
Liste des URLs ayant échoué (si il y en a). Vous pouvez relancer uniquement ces URLs plus tard.

## 🛟 Résolution de problèmes

### Si le taux de réussite est < 80%

1. **Vérifiez votre connexion internet** : Une connexion instable peut causer des timeouts

2. **Augmentez le délai entre envois** : Éditez `sender.py` ligne 298
   ```python
   time.sleep(10)  # Au lieu de 8
   ```

3. **Réduisez la fréquence de renouvellement** : Éditez `sender.py` ligne 280
   ```python
   if not DRY_RUN and i > 1 and (i - 1) % 10 == 0:  # Au lieu de 20
   ```

### Si vous obtenez beaucoup d'erreurs 422

C'est le signe que le serveur détecte et bloque les soumissions automatiques. Solutions :
1. Augmenter le délai entre envois (10-15 secondes)
2. Lancer le script par petits lots (100 entreprises à la fois)
3. Désactiver le mode headless pour ressembler plus à un vrai navigateur

### Pour désactiver le mode headless

Éditez `sender.py`, ligne 94 :
```python
# options.add_argument("--headless")  # Commenter cette ligne
```

## 📈 Optimisation

### Lancer par lots

Pour éviter les blocages, vous pouvez traiter les entreprises par lots :

1. Modifier `sender.py` pour limiter le nombre d'envois :
   ```python
   URLS_ENTREPRISES = URLS_ENTREPRISES[:100]  # Première centaine seulement
   ```

2. Ajouter les URLs traitées à `blacklist.txt` après chaque lot

3. Relancer pour le lot suivant

## ⚙️ Configuration avancée

### Changer le délai entre envois
Ligne 298 de `sender.py` :
```python
time.sleep(8)  # Modifier ce nombre (en secondes)
```

### Changer la fréquence de renouvellement de session
Ligne 280 de `sender.py` :
```python
if not DRY_RUN and i > 1 and (i - 1) % 20 == 0:  # Modifier 20
```

### Augmenter le timeout de confirmation
Ligne 141 de `sender.py` :
```python
wait = WebDriverWait(driver, 15)  # Modifier 15 (secondes)
```

## 📞 Support

Si le problème persiste après ces corrections :
1. Consultez `candidature_logs.log` pour voir les erreurs exactes
2. Vérifiez que le site n'a pas changé sa structure de formulaire
3. Essayez de faire 2-3 envois manuels pour vérifier que le site fonctionne

## 🎯 Résumé des changements critiques

| Avant | Après |
|-------|-------|
| ❌ Pas de vérification de confirmation | ✅ Attend le message "bien été envoyé" |
| ❌ `form.submit()` (non naturel) | ✅ `button.click()` (comme un humain) |
| ❌ Session unique pour tout | ✅ Renouvellement tous les 20 envois |
| ❌ Délai de 5 secondes | ✅ Délai de 8 secondes |
| ❌ Pop-up cookies non gérée | ✅ Acceptation automatique |
| ❌ Erreurs 422 non détectées | ✅ Détection et logging |

---

**Bon courage pour vos candidatures ! 🚀**
