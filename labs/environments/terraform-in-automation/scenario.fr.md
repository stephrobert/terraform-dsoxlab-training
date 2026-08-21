# Scénario : une chaîne Terraform non interactive, jugée sur ses codes de retour

**Sous-objectif d'examen visé : 3c, exécuter le workflow Terraform en automation.**

Une CI n'a pas de clavier et ne lit pas la sortie colorée : elle décide sur des codes de
retour. Ce lab fait bâtir la chaîne complète (`fmt -check`, `validate -json`, `plan -out`,
plan relu en JSON, `apply` du fichier) et montre que le plan sauvegardé trompe son monde.

## Capacité visée

Écrire un enchaînement Terraform entièrement non interactif, qui ne se bloque jamais sur un
prompt, qui sépare « rien à faire », « changements en attente » et « erreur » par le seul
code de retour, et qui applique un plan sauvegardé en sachant ce que ce fichier fige, ce
qu'il contient de sensible et quelles options y deviennent décoratives. L'enjeu n'est pas de
taper `plan -out` : c'est de savoir ce qu'une porte de revue automatisée peut conclure.

## D'où part l'apprenant

`challenge/work` contient un `main.tf` incomplet : la variable `mot_de_passe` attend son
marquage `???`, la variable `environnement` n'a délibérément aucune valeur par défaut, et la
commande `local-exec` d'une ressource `terraform_data` est trouée alors qu'elle doit rendre
l'apply assez lent pour qu'un verrou soit observable. Un `pipeline.sh` squelette tient lieu
de pipeline : ses cinq étapes sont des `???` et il lui revient de consigner les codes
relevés. Aucun `.terraform/`, aucun state, aucun `preuves/`. Lab `shell` : providers
`local`, `null` et `random`, aucune VM, aucun cloud, aucun service de CI.

## L'état à atteindre

1. La configuration est formatée, valide, initialisée sans prompt, appliquée depuis un
   fichier de plan sauvegardé et convergée, son apply durant au moins dix secondes.
2. `preuves/chaine.json` consigne le code de retour de chacune des cinq étapes de
   `pipeline.sh`, aucune ne recevant d'entrée au clavier.
3. `preuves/codes.json` consigne les trois valeurs de `plan -detailed-exitcode` (avant apply,
   après apply, sur configuration cassée) et le code de `fmt -check` sur un fichier mal indenté.
4. `preuves/prompt.json` consigne le code et le temps d'attente d'un `plan -input=false` dont
   une variable racine n'a reçu aucune valeur.
5. `preuves/plan_fige.json` consigne le sort de quatre options passées à l'apply d'un plan
   sauvegardé : celles qui font échouer la commande, celles qui sont acceptées et sans effet.
6. `preuves/verrou.json` consigne le défaut de `-lock-timeout` et le code d'un plan lancé
   pendant un apply, avec ce défaut puis avec une durée suffisante.
7. `preuves/fuite.json` désigne le chemin JSON exact où la valeur sensible sort en clair du
   plan sauvegardé, et le `.gitignore` exclut ce fichier de plan.

## Comment on le prouve

Les tests s'exécutent dans `challenge/work`, n'ouvrent ni `main.tf` ni `pipeline.sh` et ne lisent aucune sortie destinée à un humain.

- Chaque affirmation est rejouée : les tests relancent eux mêmes `fmt -check`,
  `validate -json`, `plan -detailed-exitcode`, l'apply concurrent et les quatre options du
  plan sauvegardé, puis comparent aux fichiers de `preuves/`. Rien n'est écrit en dur, et
  l'état final vient de `terraform show -json` : trois ressources en `mode: managed`.
- Trois idées reçues tombent. Le code de `fmt -check` sur un fichier mal indenté n'est pas 1.
  Un `plan -input=false` sans valeur de variable échoue aussitôt au lieu d'attendre. Et
  surtout, à l'apply d'un plan sauvegardé, seule une tentative de changer une variable lève
  une erreur : les modes de planification sont acceptés et ignorés, si bien qu'un apply lancé
  avec `-destroy` sur un plan de création crée les ressources.
- Le verrou est mesuré : avec le défaut, le plan concurrent échoue immédiatement ; avec une
  durée suffisante, il rend 0 après avoir patienté. La fuite aussi : le plan a l'air opaque,
  une relecture en JSON en sort le secret en clair. Rien de tout cela ne passe sur un
  répertoire vide ni sur un apply trop rapide.
