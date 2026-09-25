# Scénario : ce que les commandes essentielles répondent vraiment

**Sous-objectif d'examen visé : 3d, générer et examiner un plan d'exécution.**
Mobilisés en appui : 3c (valider une configuration), 3g (format et style),
4c (variables et outputs), 4h (données sensibles), 6d (state et dérive),
7a (importer de l'existant) et 7b (inspecter le state par la CLI).

L'Associate 004 est un QCM d'une heure sur Terraform 1.12 : on n'y tape rien, et
c'est le piège. Réviser un tableau de commandes donne l'illusion de savoir,
jusqu'à la question qui porte sur ce que la commande **refuse** de faire.

## Capacité visée

Établir expérimentalement le comportement exact des commandes du workflow : leur
code de retour, leur prérequis, et la frontière entre ce qu'elles modifient et ce
qu'elles se contentent de lire. La question qui gouverne le lab n'est pas « que
fait `validate` », c'est « peut-il répondre sans `init`, et qu'attrape-t-il ».

## D'où part l'apprenant

Lab de type `shell` : tout se joue dans `challenge/work`, providers `local`,
`null` et `random` seulement, aucune VM, aucun compte cloud. Le répertoire
contient un `main.tf` mal indenté et troué par des `???` (le nom d'une ressource,
un output à marquer sensible), une variable semée dans un `default`, un
`terraform.tfvars` et un `*.auto.tfvars` incomplets, et un fichier
`etat/preexistant.txt` déjà sur le disque, écrit par personne, qui attend d'être
adopté. Ni `.terraform/`, ni state, ni répertoire `preuves/`.

## L'état à atteindre

1. Le répertoire est initialisé et la configuration converge :
   `plan -detailed-exitcode` sort en 0, le state décrit les ressources attendues
   en `mode: managed`.
2. `preuves/codes.json` consigne les codes de retour observés pour six gestes :
   `validate` avant tout `init`, puis sur la configuration valide initialisée,
   puis sur une variante où un attribut n'existe pas, `fmt -check` avant et après
   reformatage, `plan -detailed-exitcode` avant convergence.
3. Quatre outputs désignent le gagnant de la cascade de précédence entre
   `default`, `TF_VAR_`, `terraform.tfvars`, `*.auto.tfvars` et `-var`.
4. Un bloc `moved {}` a renommé une ressource (ancienne adresse disparue du
   state, nouvelle présente, plan à zéro changement) et un bloc `import {}` a
   fait passer `etat/preexistant.txt` sous gestion Terraform sans toucher son
   contenu.
5. Un `removed {}` portant `lifecycle { destroy = false }` a retiré une ressource
   du state alors que le fichier qu'elle gérait existe toujours.
6. `preuves/plan-replace.json` est un plan enregistré demandant explicitement le
   remplacement d'une ressource.
7. Un output est marqué sensible, et sa valeur reste lisible en clair dans le
   state.

## Comment on le prouve

Les tests s'exécutent dans `challenge/work`, n'ouvrent jamais le `main.tf` de
l'apprenant et ne lisent aucune sortie destinée à un humain.

- Les six gestes du point 2 sont rejoués dans des copies jetables du répertoire :
  les tests relèvent eux mêmes les codes, sur votre configuration, et les
  comparent à ceux de `codes.json`. Un chiffre recopié de travers tombe. C'est
  là que tombe aussi l'idée reçue : `validate` sans `init` sort en erreur, et il
  attrape un attribut inconnu, ce que « syntaxe uniquement » laissait croire
  impossible. Ce rejeu sert surtout la justesse du lab : le jour où une version
  de Terraform change un de ces codes, c'est le rejeu qui le dit, plutôt qu'un
  candidat irréprochable qui se voit recalé.
- La précédence est lue dans `output -json`, donc dans l'état que **votre**
  apply a produit. Les tests n'appliquent rien eux mêmes : ils se contentent de
  poser dans leur environnement les `TF_VAR_` que l'énoncé fixe, faute de quoi
  la variable d'environnement retomberait sur son `default`.
- Les points 4 et 5 sont lus dans `show -json` : adresses présentes ou absentes,
  `mode: managed`, croisés avec l'existence des fichiers sur le disque. Le point
  5 ne passe que si le state a oublié la ressource pendant que le fichier
  survit, soit le contraire du défaut de `removed`.
- Le point 6 est vérifié sur le plan converti en JSON : `actions` vaut
  `["delete", "create"]` et le plan ne touche que cette adresse. Le point 7
  croise `output -json`, qui donne `"sensitive": true`, et `show -json`, où la
  même valeur apparaît en clair : le masquage est une commodité d'affichage, pas
  un chiffrement.
- Rien de tout cela ne passe sur un répertoire vide ni sur une configuration
  jamais appliquée.
