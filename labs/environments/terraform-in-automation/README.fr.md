# Une CI décide sur des codes de retour

Une chaîne d'intégration n'a pas de clavier et ne lit pas la sortie colorée. Tout
ce qu'elle sait faire, c'est lire un **code de retour**. Ce lab vous fait bâtir la
chaîne, puis **consigner** ce que Terraform répond vraiment.

## Les trois issues d'un plan

Sans option, `terraform plan` rend **0** aussi bien quand il n'y a rien à faire
que quand il reste des changements : impossible de décider.
**`-detailed-exitcode`** sépare les trois cas, et les trois ont été mesurés :

| Code | Quand |
| --- | --- |
| **0** | aucun changement, après l'apply |
| **1** | erreur, sur une configuration cassée |
| **2** | des changements en attente, avant l'apply |

## Ne jamais attendre une saisie

Une commande qui attend dans une CI n'échoue pas : elle **occupe** un agent
jusqu'au délai maximum du job. Avec `-input=false`, l'attente devient un échec
immédiat. Mesuré, sur une variable racine sans valeur :

```text
Error: No value for required variable
```

Code **1**, en **0,04 seconde**. La commande n'attend pas.

## `fmt -check` ne rend pas 1

Le code est **3**. Un pipeline qui teste `-eq 1` laisse donc passer un dépôt mal
formaté sans jamais le signaler, et celui qui oublie `-recursive` ne regarde
qu'un seul répertoire.

## Ce qu'un plan sauvegardé fige, et ce qu'il ne fige pas

C'est le point le plus contre-intuitif. Le plan fige les **valeurs de
variables** : les changer à l'apply est **refusé**.

```text
Error: Can't change variable when applying a saved plan
```

Mais les **modes de planification** y sont **acceptés et ignorés**, en silence.
Mesuré, chaque option sur un plan **frais** de création :

| Option | Résultat |
| --- | --- |
| `-var` | **erreur**, code 1 |
| `-destroy` | **accepté**, et les ressources sont **créées** |
| `-refresh=false` | accepté, sans effet |
| `-target=...` | accepté, sans effet |

Autrement dit, un `terraform apply -destroy tfplan` lancé sur un plan de création
**crée**, en code 0. Un script qui croit détruire construit.

## Le verrou

Deux exécutions concurrentes sur le même état, c'est le quotidien d'une CI.
Mesuré, un `plan` lancé pendant un `apply` :

```text
Error: Error acquiring the state lock
```

Code **1**, en **0,0 seconde** : le défaut de `-lock-timeout` est **0s**. Avec un
délai suffisant, la même commande patiente et rend **0**.

## La fuite

Le fichier de plan a l'air opaque, puisqu'il est compressé. Une relecture en JSON
en sort pourtant le secret **en clair**, y compris pour une variable marquée
`sensitive` :

```bash
terraform show -json tfplan | jq -r '.variables.mot_de_passe.value'
```

Et son nom par défaut, `tfplan`, **n'a pas d'extension** : un `.gitignore` qui ne
connaît que `*.tfplan` ne l'attrape pas.

## À vous de jouer

```bash
dsoxlab run environments-terraform-in-automation
dsoxlab check environments-terraform-in-automation
dsoxlab hint environments-terraform-in-automation
```

Il se joue **hors ligne**. Comptez une minute d'exécution : l'apply doit durer
assez longtemps pour qu'un verrou soit **observable**.

Sous-objectif d'examen visé : **3c**.

Référence : [exécuter Terraform en automation](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/terraform-en-automation/)
