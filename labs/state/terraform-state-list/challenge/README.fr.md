# L'adresse est l'identité dans le state

## La situation

**Sous-objectif d'examen visé : 1e.**

Un lab qui se contente de lister ne prouve rien. Celui-ci traite le vrai sujet de `terraform state list` : l'adresse est le seul nom d'une instance dans le state, et le piège est de croire qu'une adresse désigne une ressource unique, qu'un `grep` remplace le filtrage natif, et que les modules se comportent comme la racine.

## Capacité visée

Retrouver dans un state l'adresse exacte d'une instance dont on ne connaît que l'identifiant réel, qu'elle soit indexée par position, indexée par clé ou logée dans un module, et compter les ressources managées d'une configuration modularisée sans se tromper de chiffre.

## D'où part l'apprenant

`challenge/work` ne contient ni state ni `.terraform`. Tous les fichiers sont complets, applicables en l'état et interdits de modification, sauf un :

- `versions.tf` : `required_version = ">= 1.15.0"`, providers `hashicorp/local` et `hashicorp/random` épinglés.
- `main.tf` : `random_pet.worker` en `count = 6`, `random_pet.service` en `for_each` sur huit clés, `local_file.journal`, et une data source `local_file`. Trois ressources `random_integer` **seedées** désignent un rang, une clé et une archive ; des `locals` s'en servent pour pointer une instance de chaque famille. Le seed rend le tirage **reproductible d'une machine à l'autre**, ce qui est la condition d'une solution de référence rejouable, mais il ne l'écrit nulle part : pour savoir quelle instance porte l'identifiant publié, il faut interroger le state.
- `modules/stockage/` : `random_pet.archive` en `for_each` sur cinq clés, un `local_file` et une data source `local_file`. Ce module existe pour une seule raison : la moitié des pièges de la commande n'apparaissent que sous un module. Il est livré comme fixture en **sous-répertoire**, ce que le runtime shell ne sait faire que depuis **dsoxlab 0.1.37** : avant, son `main.tf` écrasait celui de la racine.
- `outputs.tf` : trois sorties `id_worker_recherche`, `id_service_recherche` et `id_archive_recherche` exposent la **valeur d'identifiant** des instances tirées au sort, jamais leur adresse. Cinq autres sorties se contentent de renvoyer les variables de réponse.
- `reponses.auto.tfvars` : **le seul fichier à remplir**, cinq `???`.

L'énoncé impose donc un `init` puis un `apply` avant tout : les identifiants sont générés à l'exécution, ils ne sont ni dans les fichiers ni devinables, et un nouveau tirage change les réponses.

## L'état à atteindre

1. La configuration est appliquée : le state porte 6 instances `random_pet.worker`, 8 instances `random_pet.service`, 5 instances `module.stockage.random_pet.archive`, les deux `local_file` managés et les deux data sources.
2. `adresse_worker` vaut l'adresse complète de l'instance de `random_pet.worker` dont l'`id` est celui publié par `id_worker_recherche`, sous sa forme indexée par position, crochets compris.
3. `adresse_service` vaut de même l'adresse de l'instance de `random_pet.service` correspondante, sous sa forme indexée par clé, guillemets compris.
4. `adresse_archive` vaut l'adresse **qualifiée par le module** de l'instance de `random_pet.archive` correspondante, préfixe `module.stockage.` compris.
5. `adresse_data_module` vaut l'adresse complète de la data source déclarée dans `modules/stockage/`, celle qui ne commence pas par `data` alors qu'elle en est une.
6. `nombre_managees` vaut le nombre exact de ressources en `mode: managed` du state, modules inclus et data sources exclues.
7. Un `plan` après le dernier `apply` ne propose plus rien : renseigner les réponses n'a rien fait bouger.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les fichiers de l'apprenant.

- Le test reconstruit la vérité depuis `terraform show -json` en descendant `values.root_module` puis récursivement `child_modules` : pour chaque instance il tient le couple `address` et `values.id`, plus le `mode`. Aucune sortie humaine n'est parsée.
- `terraform output -json` fournit les trois identifiants recherchés et les cinq réponses. Le test résout lui-même chaque identifiant vers son adresse dans la table construite, puis compare caractère par caractère. Une réponse juste sur la ressource mais fausse sur l'index, sur la clé ou sur le préfixe de module échoue.
- Les probabilités interdisent le hasard : 6, 8 et 5 candidats, soit une chance sur 240 de tomber juste sur les trois à l'aveugle. Les trois cibles retenues ne sont d'ailleurs ni la première position, ni la première clé de l'ordre alphabétique, précisément pour qu'« essayer la première » ne soit pas une stratégie gagnante. Le contrôle par `apply -replace` qu'envisageait la version initiale de ce scénario n'a pas été retenu : avec un tirage seedé, un remplacement redonne la même cible, et sans seed aucune solution de référence statique ne serait rejouable.
- `adresse_data_module` est comparée à l'unique instance du state en `mode: data` dont l'adresse contient `module.`. C'est exactement l'entrée que la recette `state list | grep -v ^data | wc -l` compte à tort comme managée.
- `nombre_managees` est comparé au décompte JSON des `mode: managed`. L'apprenant qui applique cette recette au `grep` rend un chiffre trop grand de un, et le test le refuse.
- `terraform plan -detailed-exitcode` rend 0 juste après le dernier `apply`.

Aucun de ces contrôles ne passe sur un répertoire vide, ni sur un state jamais interrogé : les cinq réponses ne peuvent venir que de `terraform state list`, de son option `-id` et de ses adresses de filtrage.

Référence : https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-list/

## 🎯 Challenge : retrouver une adresse quand on ne connaît que l'identifiant

### ✅ Objectif

Dans `challenge/work`, tous les fichiers sont **complets et applicables**, sauf
un : **`reponses.auto.tfvars`**, qui porte cinq placeholders.

Ces placeholders sont **applicables à dessein** : le fichier est un
`*.auto.tfvars`, donc Terraform le charge à chaque commande, et une valeur qui
ne parserait pas empêcherait l'`apply` dont vous avez besoin. Commencez donc par
appliquer, placeholders en place, sans quoi il n'y a rien à chercher :

```bash
terraform init
terraform apply
```

Trois outputs publient alors l'**identifiant** d'une instance tirée au sort, sans
jamais dire laquelle :

```bash
terraform output id_worker_recherche    # une instance de random_pet.worker  (count = 6)
terraform output id_service_recherche   # une instance de random_pet.service (for_each, 8 clés)
terraform output id_archive_recherche   # une archive du module stockage     (for_each, 5 clés)
```

À vous de remplir les cinq réponses :

1. **`adresse_worker`** : l'adresse de l'instance de `random_pet.worker` qui porte
   `id_worker_recherche`, indexée par **position**.
2. **`adresse_service`** : celle de l'instance de `random_pet.service`
   correspondante, indexée par **clé**.
3. **`adresse_archive`** : celle de l'archive correspondante, **qualifiée par le
   module**.
4. **`adresse_data_module`** : l'adresse complète de la data source déclarée dans
   `modules/stockage/`. Attention, elle ne commence pas par `data`.
5. **`nombre_managees`** : le nombre d'instances en `mode: managed` du state,
   modules **inclus**, data sources **exclues**.

Les adresses s'écrivent exactement comme `terraform state list` les affiche :
crochets, guillemets et préfixe de module compris. Sous `zsh`, quotez toute
adresse à crochets, sinon le shell la mange avant Terraform.

### 🔍 Validation

`dsoxlab check state-terraform-state-list` **reconstruit la vérité** depuis
`terraform show -json`, en descendant récursivement les `child_modules`, puis
résout lui-même chaque identifiant publié vers l'adresse qui le porte et compare
aux vôtres. Une réponse juste sur la ressource mais fausse sur l'index, sur la
clé ou sur le préfixe de module échoue.

Sont également prouvés, par exécution :

- une adresse **sans index** rend **toutes** les instances de la ressource, et
  une adresse de **module** est un filtre valide ;
- l'ordre de sortie suit la **profondeur de module**, pas l'alphabet ;
- les **quatre** diagnostics distincts d'une adresse qui ne correspond à rien,
  tous en code 1, alors qu'un `-id` sans correspondance rend **0** et une sortie
  vide ;
- la recette `state list | grep -v ^data | wc -l` rend bien **un de plus** que le
  vrai comptage : c'est la data source du module qu'elle compte à tort ;
- `plan -detailed-exitcode` rend 0 : lire le state ne change rien.

Bloqué ? `dsoxlab hint state-terraform-state-list`.
