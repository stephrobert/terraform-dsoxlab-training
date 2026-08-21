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

L'apprenant lance `terraform init` puis `terraform apply`. Terraform crée les premières
ressources, échoue sur la dernière, et rend la main avec un code de retour non nul. Il a
alors sous les yeux un state partiel : son point de départ, pas un accident à effacer.

## L'état à atteindre

- La cause de l'échec est corrigée dans la configuration, sans supprimer la ressource
  fautive ni la neutraliser en la commentant.
- Toutes les ressources déclarées sont présentes dans le state.
- Les ressources créées lors du premier `apply` portent **les mêmes identifiants**
  qu'avant la réparation : elles n'ont été ni détruites, ni remplacées.
- Le répertoire de travail est convergé : un nouveau `plan` ne propose plus rien.

## Comment on le prouve

Par de l'état structuré et des codes de retour, jamais par le code de l'apprenant ni par
le texte d'un message d'erreur.

- **Après l'échec** : `terraform show -json` expose un state qui contient les ressources
  déjà créées et **pas** la ressource fautive. Le test compte les adresses présentes.
- **Empreinte de reprise** : les identifiants des ressources déjà créées sont relevés
  après l'échec, puis comparés après la réparation. Toute valeur différente signe une
  destruction suivie d'une recréation, donc un échec.
- **Convergence** : `terraform plan -detailed-exitcode` sort en **0**. Le code 2
  (changements en attente) et le code 1 (erreur) sont l'un comme l'autre des échecs.
- **Effet réel** : le fichier produit par la ressource initialement fautive existe sur le
  disque, ce qui prouve que la réparation a bien fait aboutir l'exécution.
