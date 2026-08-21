# Scénario : léguer une infra sans la détruire, avec le bloc removed

**Sous-objectifs d'examen visés : 1e (gérer le state) et 4c (refactorer une configuration).**

Ce lab traite le contresens le plus coûteux du bloc `removed` : croire qu'il se
contente de retirer du state et que `destroy = true` serait l'option à ajouter
pour aller plus loin. C'est l'inverse. Détruire est le comportement **par
défaut** ; `destroy = false` est l'opt-out qui préserve l'objet réel.

## Capacité visée

Sortir des ressources du state d'une configuration en production, en décidant
pour chacune si l'objet réel doit survivre ou disparaître, et savoir quand le
bloc `removed` ne suffit pas et qu'il faut retomber sur `terraform state rm`.

## D'où part l'apprenant

Dans `challenge/work`, un `main.tf` complet et applicable décrit un lot
d'artefacts locaux en fin de vie : `random_pet.jeton` (la source de noms, qui
reste gérée), `local_file.rapports` en `for_each` sur deux clés,
`local_file.bacs` en `for_each` sur trois clés, `local_file.cache` et
`local_file.journaux`. Aucun state n'existe : le premier geste est un `init`
puis un `apply`, qui crée sept fichiers et huit adresses.

Un second fichier, `migration.tf`, contient deux blocs `removed` à trous
(`from = ???`, corps `???`) et, en commentaire, l'affirmation fausse qui sert de
piège : « le bloc `removed` retire du state ; ajoutez `destroy = true` si vous
voulez en plus détruire l'objet ». Le plan la démentira.

Ces deux blocs sont eux-mêmes **livrés en commentaire**, ce qui rend la
configuration applicable telle quelle : l'apprenant les décommente quand il en a
besoin. Un troisième bloc, celui des journaux, est à écrire de zéro.

## L'état à atteindre

1. Les deux instances de `local_file.rapports` ont disparu du state, mais leurs
   deux fichiers existent toujours sur le disque, contenu intact : elles ont été
   oubliées, pas détruites.
2. `local_file.cache` a disparu du state **et** son fichier a disparu du disque.
   C'est le même bloc `removed`, sans `destroy = false` : la destruction est le
   défaut, et la comparaison avec le point 1 le prouve dans le même dépôt.
3. Le bloc `resource` de chaque ressource oubliée a été retiré de `main.tf`.
   Laisser les deux en place fait échouer le plan sur `Removed resource still
   exists` : le bloc `removed` n'est pas un interrupteur, c'est la trace d'une
   suppression déjà faite dans la configuration.
4. Seule l'instance `local_file.bacs["beta"]` est sortie du state ; les deux
   autres y sont toujours et leurs trois fichiers sont intacts. Le bloc
   `removed` refuse une clé d'instance dans son `from` (`Resource instance keys
   not allowed`) : cette granularité n'existe que via
   `terraform state rm 'local_file.bacs["beta"]'`.
5. Le `for_each` de `local_file.bacs` ne liste plus `beta`. Sans cet alignement,
   Terraform recréerait aussitôt l'instance sortie du state, et le fichier légué
   serait écrasé.
6. La migration de `local_file.journaux` est **préparée mais non appliquée** :
   son bloc `resource` est retiré, son bloc `removed` avec `destroy = false` est
   écrit, et le plan l'annonce sans que l'apprenant l'exécute. C'est l'argument
   de la documentation pour préférer `removed` à `state rm` : l'opération est
   prévisualisable, donc relisible en revue de code.

## Comment on le prouve

Les tests interrogent l'état structuré, jamais le fichier `.tf` de l'apprenant :

- `terraform show -json` : quatre adresses en `mode: managed` et pas une de
  plus, `random_pet.jeton`, `local_file.bacs["alpha"]`, `local_file.bacs["gamma"]`
  et `local_file.journaux`. L'absence de `local_file.rapports`, de
  `local_file.cache` et de `local_file.bacs["beta"]` y est vérifiée adresse par
  adresse.
- Le système de fichiers tranche entre oubli et destruction : les six fichiers
  légués existent encore et leur contenu porte toujours le jeton de
  `random_pet.jeton` lu dans le state, tandis que le fichier de
  `local_file.cache` est bien absent.
- Le plan converti en JSON contient exactement un changement non `no-op` :
  `actions: ["forget"]` sur `local_file.journaux`. Cette action n'apparaît que
  si le bloc `removed` porte `destroy = false` ; avec le défaut, la même
  configuration produirait `actions: ["delete"]`.
- `terraform plan -detailed-exitcode` sort donc en **2**, et aucune entrée du
  plan ne concerne `local_file.bacs` : ni `create` sur `beta`, preuve que le
  `for_each` a été aligné après le `state rm`, ni `delete` sur les deux autres.
- Deux contrôles de comportement, joués dans une copie temporaire et sans
  toucher au travail de l'apprenant, prouvent ce que le lab enseigne : un bloc
  `removed` visant `local_file.bacs["alpha"]` échoue sur `Resource instance keys
  not allowed`, ce qui justifie le passage par `terraform state rm` ; et le même
  bloc privé de `destroy = false` planifie `delete` sur chaque instance restante.
  S'ils virent au rouge, c'est le lab qu'il faut revoir, pas la copie.
