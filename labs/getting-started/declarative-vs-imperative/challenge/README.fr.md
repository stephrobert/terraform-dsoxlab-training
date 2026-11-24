# Prouver l'idempotence là où le script impératif diverge

## La situation

**Sous-objectif d'examen visé : 1b `plan` (prouver l'idempotence, détecter une dérive et la corriger).**

Un script de provisionnement impératif est fourni et diverge dès qu'on le
rejoue. L'apprenant doit obtenir le même résultat en Terraform, puis démontrer
par le plan que le second passage est un non-événement.

## Capacité visée

Traduire une intention exprimée en étapes d'exécution vers une configuration qui
décrit un état cible, puis établir la propriété qui sépare les deux approches :
la convergence. L'apprenant doit produire la preuve machine de cette convergence
et non l'affirmer, et corriger une dérive externe sans modifier son code.

## D'où part l'apprenant

`challenge/work` contient `imperatif.sh`, un script fourni qui fabrique un
répertoire de sortie, y écrit un rapport et y inscrit un identifiant tiré au
hasard à chaque appel. Rejoué, il produit un identifiant différent et empile son
rapport au lieu de le remplacer : l'état obtenu dépend du nombre d'exécutions.
Une configuration Terraform incomplète l'accompagne, avec les providers `local`,
`random` et `null` et des arguments à compléter, notamment ceux qui décident du
caractère stable ou non des valeurs générées. Il n'y a ni `.terraform/`, ni
state, ni fichier de verrouillage. Le script se lit, il ne se corrige pas.

## L'état à atteindre

1. Le projet est initialisé : le fichier de verrouillage des dépendances est
   présent et les providers `local`, `random` et `null` y sont enregistrés.
2. Un state existe et référence trois ressources gérées : celle qui fixe
   l'identifiant aléatoire, celle qui matérialise le rapport sur le disque,
   celle dont le déclencheur dépend de l'identifiant.
3. Le fichier de rapport existe sur le disque et son contenu porte
   l'identifiant enregistré dans le state.
4. Deux sorties sont exposées : l'identifiant, non vide, et le chemin du
   rapport, qui désigne le fichier présent.
5. Immédiatement après l'application, un nouveau plan n'annonce aucune action.
6. Le fichier de rapport est supprimé hors de Terraform : le plan annonce alors
   une seule création et aucun remplacement de l'identifiant.
7. Après convergence, le fichier est de retour et l'identifiant vaut toujours la
   valeur relevée avant la dérive.

## Comment on le prouve

L'inventaire du state est lu avec `terraform show -json` : on y cherche les
adresses des trois ressources gérées, l'identifiant et le chemin du rapport. Les
sorties sont lues avec `terraform output -json`, jamais dans la sortie humaine.
Le rapport est constaté sur le disque puis confronté aux attributs du state.

L'idempotence est établie par `terraform plan -detailed-exitcode`, dont le code
de sortie doit valoir 0 juste après l'application. La dérive l'est de la même
façon : après suppression du fichier, le même appel doit sortir en 2. Le plan est
ensuite enregistré avec `-out`, relu par `terraform show -json`, et l'on exige
une seule entrée en création, sur la ressource de fichier et sur aucune autre.

La correction est appliquée sans modifier le code : l'identifiant relu par
`terraform output -json` doit être identique à celui capturé avant la dérive, et
un dernier `terraform plan -detailed-exitcode` doit revenir à 0. Aucun contrôle
ne lit le contenu des fichiers `.tf` écrits par l'apprenant.

## 🎯 Challenge : prouver l'idempotence là où le script diverge

### Point de départ

`challenge/work` contient quatre fichiers :

- `imperatif.sh` : **fourni, à lire, pas à corriger**. Il fabrique un répertoire
  de sortie, y écrit un rapport et y inscrit un identifiant tiré à chaque appel.
  Rejouez-le deux fois et comparez : l'identifiant change, et le rapport
  s'allonge.
- `versions.tf` : **complet**. Il épingle `local`, `null` et `random`.
- `main.tf` : **troué**. Trois ressources, dont les arguments qui décident du
  caractère stable ou non des valeurs générées.
- `outputs.tf` : **troué**. Deux sorties.

Il n'y a ni `.terraform/`, ni state, ni fichier de verrouillage.

### ✅ Objectif

Obtenez en Terraform le même résultat que le script, puis prouvez ce qui les
sépare.

1. **`random_string.identifiant`** : huit caractères, ni majuscules ni
   caractères spéciaux, et un `keepers` qui le rende **stable**.
2. **`local_file.rapport`** : son contenu est **construit** à partir de
   l'identifiant, et le fichier est **remplacé**, jamais empilé.
3. **`null_resource.empreinte`** : son déclencheur dépend de l'identifiant.
4. **Les deux sorties** : l'identifiant, et le chemin du rapport.

Puis, sans modifier votre code : supprimez le rapport à la main, constatez la
dérive, et laissez Terraform réparer.

### 🧭 Ce que le lab vous fait constater

- **Deux passages du script donnent deux identifiants.** Deux `apply` du même
  code n'en donnent qu'un : la valeur est mémorisée dans le state.
- **Le rapport impératif s'allonge, le rapport déclaratif est remplacé.** L'un
  décrit un historique, l'autre un état.
- **Après suppression du rapport, le plan annonce une seule création.**
  L'identifiant n'est pas retiré, et la `null_resource` n'est pas remplacée : la
  dérive se répare là où elle a eu lieu.
- **L'identifiant survit à la réparation.** C'est `keepers` qui le garantit,
  et rien d'autre.

### 🔍 Validation

```bash
dsoxlab check getting-started-declarative-vs-imperative
```

Huit tests lisant `terraform show -json`, `output -json`, un plan enregistré
avec `-out` et relu en JSON, et des codes retour. Le dernier compare les deux
approches sur le même geste : le script rejoué diverge, la configuration rejouée
ne bouge plus. Aucun ne lit vos `.tf`.
