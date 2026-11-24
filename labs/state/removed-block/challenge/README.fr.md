# Léguer une infra sans la détruire, avec le bloc removed

## La situation

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

## 🎯 Challenge : un lot en fin de vie, quatre décisions différentes

### 📦 Le point de départ

`challenge/work` contient un projet complet, mais **jamais appliqué**. C'est à
vous de le mettre en route :

```bash
terraform init
terraform apply
```

Huit adresses entrent alors dans le state, et sept fichiers apparaissent sur le
disque :

| Adresse | Fichier | Ce qu'il doit devenir |
| --- | --- | --- |
| `random_pet.jeton` | (aucun) | reste géré, du début à la fin |
| `local_file.rapports["mensuel"]` et `["annuel"]` | `rapport-*.txt` | **légués** : hors du state, fichiers conservés |
| `local_file.bacs["beta"]` | `bac-beta.txt` | **légué**, lui seul parmi les trois bacs |
| `local_file.bacs["alpha"]` et `["gamma"]` | `bac-*.txt` | restent gérés |
| `local_file.cache` | `cache.txt` | **détruit**, fichier compris |
| `local_file.journaux` | `journaux.txt` | migration **écrite mais pas appliquée** |

Deux fichiers, deux statuts : `main.tf` est complet et **à modifier** (retirer un
bloc `resource`, retirer une clé d'un `for_each`), `migration.tf` porte deux
blocs `removed` **livrés en commentaire** et troués de `???`. Un troisième bloc
est à écrire de zéro.

**La note laissée dans `migration.tf` est fausse.** Elle prétend qu'un bloc
`removed` se contente de retirer du state et qu'il faudrait `destroy = true`
pour détruire. Ne la croyez pas : lisez le plan.

### ✅ Objectif

Mener la migration de ce lot en décidant, ressource par ressource, si l'objet
réel survit ou disparaît, et employer la bonne voie pour chaque grain.

### 📋 Ce qu'il faut obtenir

1. Le state ne porte plus que **quatre adresses** : `random_pet.jeton`,
   `local_file.bacs["alpha"]`, `local_file.bacs["gamma"]` et
   `local_file.journaux`.
2. Les **six fichiers légués** existent toujours, avec le contenu écrit lors du
   premier `apply` : les deux rapports, les trois bacs et le journal.
3. `cache.txt` a **disparu** du disque, et son adresse du state.
4. Seule la clé `beta` est sortie de `local_file.bacs`, et elle **ne figure plus
   dans le `for_each`** : sans cet alignement, Terraform recrée l'instance et
   écrase le fichier légué.
5. La migration de `local_file.journaux` est **préparée, pas appliquée** : son
   bloc `resource` a disparu, son bloc `removed` est écrit, et
   `terraform plan -detailed-exitcode` sort en **code 2** avec un unique
   changement, `forget` sur cette adresse.

### ⚠️ Le cœur du sujet

Deux frontières décident de tout, et aucune n'est devinable :

| Ce que vous voulez | Ce qu'il faut écrire |
| --- | --- |
| Léguer un objet (il survit) | `removed` + `lifecycle { destroy = false }` |
| Supprimer un objet | `removed` seul, ou `destroy = true` |
| Sortir **une seule instance** d'un `for_each` | `terraform state rm`, puis retirer la clé du `for_each` |

Le bloc `removed` refuse une clé d'instance dans son `from`
(`Resource instance keys not allowed`), et il **détruit par défaut**. Une erreur
sur ce point ne se rattrape pas : le fichier est supprimé, et les tests le
verront.

### 🔍 Validation

`dsoxlab check state-removed-block` prouve, par exécution :

- le state porte **exactement** les quatre adresses attendues ;
- les six fichiers légués existent et portent toujours le **jeton lu dans le
  state** : un fichier recréé aurait un autre contenu ;
- `cache.txt` est bien absent, du disque comme du state ;
- aucun changement en attente sur les bacs, ce qui prouve l'alignement du
  `for_each` ;
- exactement un changement en attente, `forget` sur `local_file.journaux`, et
  `plan -detailed-exitcode` en **code 2** ;
- deux contrôles de comportement joués dans une copie temporaire, sans toucher à
  votre travail.

Aucun test n'ouvre vos fichiers `.tf` : ils lisent le state, le disque et des
plans enregistrés.

Bloqué ? `dsoxlab hint state-removed-block`.
