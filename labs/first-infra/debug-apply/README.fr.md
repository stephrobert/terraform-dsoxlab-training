# Reprendre après un apply qui a échoué, sans refaire le travail

Un `terraform apply` qui s'arrête en cours de route ne laisse pas un désordre :
il laisse un **état partiel et cohérent**. Terraform est conçu pour reprendre là
où il s'est arrêté, et pourtant le premier réflexe est presque toujours de tout
détruire pour repartir de zéro.

Sur ce lab, cela coûte quelques secondes. Sur une base de données, cela coûte
les données.

## Le state ne dit pas ce qu'on croit

Voici le fait que ce lab existe pour faire constater. Après un échec, la
ressource fautive **n'est pas absente** du state. Elle y figure, marquée
`tainted` :

```console
$ terraform show -json | jq '.values.root_module.resources[] | {address, tainted}'
{"address": "random_pet.identifiant", "tainted": null}
{"address": "local_file.inventaire",  "tainted": null}
{"address": "null_resource.rapport",  "tainted": true}
```

`tainted` veut dire : « cet objet a été créé, quelque chose a échoué ensuite, je
ne sais pas dans quel état il est, je le **remplacerai** au prochain apply ».

C'est une nuance qu'on lit rarement, et elle change tout. On n'est pas devant
deux ressources créées et une manquante, mais devant deux ressources **saines**
et une **à reprendre**.

## Corriger la cause, et rien d'autre

L'objectif est de réparer **la cause**. Quatre réflexes viennent avant, et tous
sont faux :

| Réflexe | Pourquoi c'est faux |
| --- | --- |
| supprimer la ressource fautive | l'échec disparaît, le besoin aussi |
| la commenter | pareil, avec un souvenir dans le dépôt |
| `mkdir` à la main | la configuration reste fausse, elle échouera ailleurs |
| `destroy` puis tout refaire | détruit deux ressources saines pour en réparer une |

Le troisième est le plus intéressant, parce qu'il **marche**. L'apply passe, le
plan converge, et tout est vert sur le poste de celui qui a tapé la commande.
C'est exactement pour cela que le dernier test du lab rejoue la configuration
dans un répertoire **vierge** : une correction qui ne vit que dans le shell de
son auteur n'est pas une correction.

## L'empreinte de reprise

Comment prouver qu'on a **repris** plutôt que **refait** ? L'état final est le
même dans les deux cas. Ce qui les distingue, ce sont les identifiants :

```console
$ terraform show -json | jq -r '.values.root_module.resources[]
    | "\(.address) \(.values.id)"'
```

Une ressource reprise garde son identifiant. Une ressource recréée en reçoit un
autre. Le lab relève ceux du state fourni, puis les compare après la réparation :
toute valeur différente signe une destruction suivie d'une recréation.

## Où regarder quand la cause n'est pas évidente

Le message d'erreur dit *que* ça a échoué, rarement *pourquoi*. Deux outils
valent mieux que relire le code :

```bash
terraform plan -json | jq 'select(.@level == "error")'
```

```bash
TF_LOG=DEBUG TF_LOG_PATH=/tmp/tf-debug.log terraform apply
```

`TF_LOG_PATH` compte autant que `TF_LOG` : sans lui, la trace part sur le
terminal, se mélange à la sortie normale et défile. Avec lui, elle est dans un
fichier qu'on relit à froid.

## À vous de jouer

```bash
dsoxlab run first-infra-debug-apply
dsoxlab check first-infra-debug-apply
dsoxlab hint first-infra-debug-apply
```

Le lab se joue **hors ligne**, sur les providers `random`, `local` et `null` :
l'échec est déterministe et se reproduit à l'identique sur n'importe quel poste.
Le state partiel est **fourni** : vous arrivez comme on arrive sur un incident,
devant un état que vous n'avez pas produit.

Sous-objectif d'examen visé : **1e**, avec appui sur **1c**.

Référence : [déboguer un apply](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/debug-apply/)
