# `terraform state list` : l'adresse est l'identité dans le state

`terraform state list` liste les **instances** que Terraform gère, une par ligne,
sous la forme de leur **adresse**. Cette adresse est le seul nom qu'une instance
possède dans le state : c'est elle que réclament `state show`, `state mv`,
`state rm`, `import` et `-replace`. Ce tutoriel montre comment la lire et
comment filtrer ; le challenge vous fera retrouver des adresses dont vous ne
connaîtrez que l'identifiant réel.

## Ressource, instance, adresse

La distinction qui explique tout le reste : une **ressource** est ce que vous
déclarez, une **instance** est ce que Terraform crée. Un bloc `resource` en
`count = 3` est **une** ressource et **trois** instances, donc trois lignes et
trois adresses :

```bash
terraform state list
```

```text
data.local_file.lecture
local_file.rapport
random_pet.noeud[0]
random_pet.noeud[1]
random_pet.noeud[2]
random_pet.zone["eu-west"]
random_pet.zone["us-east"]
module.reseau.random_pet.sous_reseau["a"]
module.reseau.data.local_file.relecture
```

Trois formes d'adresses cohabitent ici, et il faut savoir les écrire :

| Déclaration | Adresse d'une instance |
| --- | --- |
| ressource simple | `local_file.rapport` |
| `count` | `random_pet.noeud[0]`, indexée par **position** |
| `for_each` | `random_pet.zone["eu-west"]`, indexée par **clé**, guillemets compris |
| dans un module | `module.reseau.random_pet.sous_reseau["a"]` |
| data source | `data.local_file.lecture` |

## L'ordre de la sortie n'est pas alphabétique

La liste est triée par **profondeur de module**, puis par ordre alphabétique. Les
instances de la configuration racine sortent donc **en premier**, celles des
modules **ensuite**, du moins profond au plus profond. Dans l'exemple ci-dessus,
`module.reseau.*` passe après `random_pet.zone`, ce qu'un tri purement
alphabétique interdirait. C'est utile à savoir dès qu'on lit une longue sortie :
le bas de la liste est la partie modularisée.

## Filtrer : la commande accepte des motifs, pas seulement des noms complets

L'argument d'adresse est un **filtre**, et il travaille par famille. Trois usages
que l'on croit souvent impossibles :

```bash
terraform state list random_pet.noeud       # les 3 instances de la ressource
terraform state list 'random_pet.noeud[0]'  # une seule instance
terraform state list module.reseau          # tout le contenu du module
```

Une adresse **sans index** ne désigne donc pas une instance unique : elle rend
**toutes** les instances de la ressource. Et une adresse de **module** est un
filtre parfaitement valide, qui descend dans les sous-modules. C'est le filtrage
le plus utile de la commande, et celui qu'on remplace à tort par un `grep`.

Plusieurs adresses se cumulent, et la sortie suit alors **l'ordre des
arguments**, pas l'ordre trié.

**Les crochets se quotent, toujours.** Sous `zsh`, `terraform state list
random_pet.noeud[0]` échoue avant même d'atteindre Terraform, avec un
`no matches found` : les crochets sont un motif de nom de fichier. Les guillemets
simples règlent le problème pour toute adresse indexée ou à clé.

## Chercher par identifiant avec `-id`

Quand vous connaissez l'identifiant réel d'un objet mais pas son adresse,
`-id` filtre sur la valeur de l'attribut `id` :

```bash
terraform state list -id=deep-foxhound
```

```text
random_pet.noeud[0]
```

C'est le geste central du challenge : passer d'un identifiant à une adresse.
`-id` se combine à une adresse, et l'on obtient alors l'**intersection** des deux
filtres.

## Les diagnostics, et l'asymétrie qui compte

Une adresse qui ne correspond à rien produit une **erreur** et un code de retour
**1**, avec quatre messages distincts selon ce qui manque :

| Adresse fournie | Diagnostic |
| --- | --- |
| ressource absente | `Unknown resource` |
| instance absente d'une ressource existante | `Unknown resource instance` |
| module absent | `Unknown module` |
| type seul, sans nom | `Invalid address` |

Un **`-id` sans correspondance**, lui, ne produit **aucune erreur** : sortie
vide, code de retour **0**. Cette asymétrie décide de la façon dont on scripte la
commande : un filtre par adresse se teste sur son code de retour, un filtre par
`-id` se teste sur le fait que la sortie soit vide ou non.

## Compter les ressources gérées, sans se tromper

La recette qui circule est `terraform state list | grep -v ^data | wc -l`. Elle
est fausse dès qu'un module contient une data source, car l'adresse de celle-ci
commence par `module.`, pas par `data`. Le comptage se fait sur la sortie
machine, en filtrant sur le champ `mode` et en descendant les modules :

```bash
terraform show -json | jq '[.values.root_module
  | .. | .resources? // empty | .[]
  | select(.mode == "managed")] | length'
```

C'est un cas d'école du principe qui gouverne ces labs : on assère sur la sortie
**structurée**, jamais sur une sortie destinée à un humain.

## À vous de jouer

Vous savez distinguer ressource et instance, écrire les quatre formes
d'adresses, filtrer par ressource, par instance et par module, chercher par
`-id`, et compter les ressources gérées sans vous faire piéger par une data
source de module. Le challenge publie trois identifiants et vous demande les
adresses correspondantes, dans un projet qui mélange `count`, `for_each` et un
module.

```bash
dsoxlab run state-terraform-state-list
dsoxlab check state-terraform-state-list
dsoxlab hint state-terraform-state-list
```

Sous-objectif d'examen visé : **1e** (inspecter le state), niveau Associate.

Référence : [terraform state list](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-list/)
