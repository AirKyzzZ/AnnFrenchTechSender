# 🐛 Mode Debug Visuel - Mode d'emploi

## Pourquoi utiliser ce mode ?

Le mode debug visuel vous permet de **VOIR EXACTEMENT** ce qui se passe :
- Le navigateur s'ouvre devant vous (pas caché)
- Chaque action est ralentie et expliquée
- Vous pouvez observer les formulaires, les soumissions, les confirmations
- Parfait pour comprendre pourquoi ça ne fonctionne que sur certaines entreprises

## 🚀 Comment lancer

```bash
python sender_debug_visuel.py
```

## 📋 Ce qui va se passer

1. **Le script vous demande confirmation** (car il envoie de vraies candidatures)
2. **Chrome s'ouvre en mode visible** (vous voyez la fenêtre)
3. **Le script traite 3 entreprises** avec des pauses entre chaque étape :
   - Chargement de la page (pause 3s)
   - Remplissage du formulaire (lent, champ par champ)
   - Soumission
   - Vérification du message de confirmation (pause 5s)
   - Analyse du résultat

4. **À chaque étape**, le script affiche :
   ```
   [ÉTAPE 1/7] Chargement de la page...
   ⏸️  Page en cours de chargement
      ... 3 secondes
      ... 2 secondes
      ... 1 seconde
      ... ✓ C'est parti !
   ✓ Page chargée
   ```

5. **Après chaque envoi**, vous voyez :
   - ✅ SUCCÈS si le message "Votre message a bien été envoyé" apparaît
   - ❌ ÉCHEC si pas de message de confirmation
   - Le contenu de la page (300 premiers caractères)

## 🔍 Ce qu'il faut observer

### Pendant le remplissage du formulaire
- Est-ce que tous les champs se remplissent correctement ?
- Y a-t-il une pop-up de cookies qui apparaît ?
- Y a-t-il d'autres éléments qui bloquent le formulaire ?

### Après la soumission (CRUCIAL)
- L'URL change-t-elle après le submit ?
- Voyez-vous un message vert "Votre message a bien été envoyé !" ?
- Ou voyez-vous une page d'erreur ?
- La page reste-t-elle identique sans message ?

## 📊 Interprétation des résultats

### Cas 1 : Message vert "Votre message a bien été envoyé"
✅ **L'envoi a RÉELLEMENT fonctionné**
→ Vous devriez recevoir un email de confirmation

### Cas 2 : Pas de message, page reste identique
❌ **Le formulaire est soumis mais PAS envoyé**
→ Problème : le site rejette silencieusement la soumission
→ Raisons possibles : CSRF token, détection de bot, rate limiting

### Cas 3 : Erreur 422 ou message "rejetée"
❌ **Le serveur refuse explicitement la soumission**
→ Le site détecte un problème (bot, token manquant, etc.)

### Cas 4 : Erreur de formulaire non trouvé
❌ **La structure de la page est différente**
→ Certaines entreprises peuvent avoir un formulaire différent

## 🎯 Que faire avec les résultats

### Si TOUS les envois échouent
→ Le problème est dans le script ou la méthode d'envoi

### Si SEULEMENT le 1er réussit
→ Problème de session/cookies entre les envois

### Si CERTAINS réussissent de façon aléatoire
→ Problème de rate limiting ou détection de bot

### Si AUCUN ne réussit mais le script dit "succès"
→ Le script ne vérifie pas correctement la confirmation
→ C'est exactement ce qui se passe actuellement !

## 📝 Logs détaillés

Les logs détaillés sont sauvegardés dans :
```
candidature_debug.log
```

## 💡 Astuce

Pendant l'exécution, vous pouvez :
- Prendre des screenshots de ce que vous voyez
- Noter les différences entre les envois qui réussissent et ceux qui échouent
- Vérifier votre boîte mail pendant/après pour voir combien de confirmations arrivent réellement

## ⏭️ Prochaines étapes

Après avoir lancé le debug visuel, vous saurez :
1. Si le problème vient du script qui ne détecte pas les échecs
2. Si certaines entreprises ont des formulaires différents
3. Si le site bloque après X soumissions
4. Si les "succès" dans les logs sont des vrais succès ou des faux positifs

---

**Lancez maintenant :**
```bash
python sender_debug_visuel.py
```

**Et observez attentivement ce qui se passe dans le navigateur !** 👀
