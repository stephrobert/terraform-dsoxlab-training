# Scénario : prouver l'idempotence là où le script impératif diverge

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
