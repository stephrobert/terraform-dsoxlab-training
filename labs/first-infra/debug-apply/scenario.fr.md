# Scénario : reprendre un apply interrompu à mi-chemin

**Sous-objectif d'examen visé : 1e (interpréter et manipuler le state après un apply partiel), avec appui sur 1c (exécuter `terraform apply`).**

Un `terraform apply` s'arrête sur une erreur après avoir créé une partie des ressources.
Le state n'est ni vide ni complet : il est partiel, et pourtant cohérent.

## Capacité visée

Diagnostiquer un `apply` qui échoue en cours de route, corriger la cause, puis converger
vers l'état cible **sans repartir de zéro**. C'est le geste qui sépare le débutant du
professionnel : le réflexe naturel est de tout détruire et de recommencer, alors que
Terraform est conçu pour reprendre là où il s'est arrêté. Détruire ce qui a réussi coûte
du temps en lab, et des données en production.

La capacité se décompose en trois temps :

1. **Constater** que l'échec est partiel, en lisant le state et non le message d'erreur.
2. **Localiser** la ressource fautive, avec `terraform plan -json`, ou `TF_LOG=DEBUG`
   couplé à `TF_LOG_PATH` pour isoler les logs dans un fichier.
3. **Réparer puis converger**, en vérifiant que les ressources déjà créées ne sont ni
   détruites ni recréées.

## D'où part l'apprenant

Le répertoire `challenge/work` contient une configuration Terraform qui n'utilise que des
providers locaux (`random`, `local`, `null`) : aucune VM, aucun cloud, aucun accès réseau.
L'échec est donc **déterministe** et reproductible à l'identique sur n'importe quel poste.
La configuration décrit une courte chaîne de ressources : un identifiant aléatoire, un
fichier généré à partir de cet identifiant, puis une ressource d'exécution locale qui
dépend des deux précédentes. Cette dernière échoue volontairement, parce qu'elle écrit
dans un répertoire que rien ne crée.

**Le state partiel est fourni**, l'apprenant n'a donc pas à provoquer l'échec lui-même :
il arrive comme on arrive sur un incident, devant un état qu'il n'a pas produit.

Ce state réserve une surprise que le lab existe pour faire constater : la ressource
fautive **n'est pas absente**. Elle figure dans le state, marquée `tainted`. Terraform
sait qu'elle est dans un état douteux et la **remplacera** au prochain apply. C'est la
première chose à regarder, et elle change la façon de reprendre :

```bash
terraform show -json | jq '.values.root_module.resources[] | {address, tainted}'
```

## L'état à atteindre

- La cause de l'échec est corrigée dans la configuration, sans supprimer la ressource
  fautive ni la neutraliser en la commentant.
- La ressource fautive n'est plus marquée `tainted` : elle a abouti.
- Toutes les ressources déclarées sont présentes dans le state.
- Les ressources créées avant l'échec portent **les mêmes identifiants** qu'avant la
  réparation : elles n'ont été ni détruites, ni remplacées.
- Le répertoire de travail est convergé : un nouveau `plan` ne propose plus rien.
- La configuration se rejoue **sur un répertoire vierge**.

## Comment on le prouve

Par de l'état structuré et des codes de retour, jamais par le code de l'apprenant ni par
le texte d'un message d'erreur.

- **Le marquage a disparu** : la ressource initialement fautive figure dans le state
  sans `tainted`. C'est la preuve qu'elle a abouti, et non qu'on l'a fait disparaître.
- **La ressource existe toujours** : la supprimer de la configuration ferait aussi
  disparaître l'échec, et c'est la mauvaise réponse la plus tentante.
- **Empreinte de reprise** : les identifiants des ressources déjà créées sont relevés
  dans le state fourni, puis comparés après la réparation. Toute valeur différente signe
  une destruction suivie d'une recréation, donc un échec.
- **Effet réel** : le fichier produit par la ressource initialement fautive existe sur le
  disque, ce qui prouve que la réparation a bien fait aboutir l'exécution.
- **Convergence, et rejeu à neuf** : `terraform plan -detailed-exitcode` sort en **0**,
  et la configuration est rejouée dans un répertoire **vierge**. Un `mkdir` lancé à la
  main ferait passer l'apply sur le poste de l'apprenant et nulle part ailleurs.
