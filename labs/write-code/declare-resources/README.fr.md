# Le cycle de vie d'une ressource se lit dans le plan

Déclarer un bloc `resource {}` est trivial. Dire, **avant** d'appliquer, si
Terraform va mettre la ressource à jour en place ou la détruire pour la recréer,
ne l'est pas. C'est pourtant ce que l'examen interroge, et ce qui évite les
mauvaises surprises en production. La réponse est toujours dans le plan, au
format JSON.

Ce tutoriel construit un exemple **jetable**, un artefact versionné, et lit ses
quatre opérations de cycle de vie dans le tableau `resource_changes[].actions`.
Tout tourne sur `local`, `random` et la ressource intégrée `terraform_data`,
sans cloud.

## Les quatre opérations, et leur signature

Terraform ne fait que quatre choses à une ressource, et chacune a une signature
dans le plan JSON :

| Opération | `actions` dans le plan |
|---|---|
| Créer | `["create"]` |
| Mettre à jour **en place** | `["update"]` |
| Remplacer (détruire puis créer) | `["delete", "create"]` |
| Détruire | `["delete"]` |

Une cinquième valeur, `["no-op"]`, signale qu'il n'y a rien à faire. Tout le
sujet tient à distinguer une **mise à jour en place** d'un **remplacement** :
l'une est indolore, l'autre recrée l'objet.

## Monter l'exemple

Dans un répertoire à part, trois ressources et deux variables :

```hcl
variable "niveau" {
  type    = string
  default = "beta"
}

variable "cycle" {
  type    = number
  default = 1
}

resource "random_pet" "serie" {
  length  = 2
  keepers = { cycle = var.cycle }
}

resource "local_file" "paquet" {
  filename = "${path.module}/out/paquet-${random_pet.serie.id}.txt"
  content  = "serie=${random_pet.serie.id}\n"

  lifecycle {
    create_before_destroy = true
  }
}

resource "terraform_data" "jeton" {
  input            = var.niveau
  triggers_replace = random_pet.serie.id
}
```

Deux points de vocabulaire. Le couple **type + nom** (`terraform_data.jeton`) est
l'**adresse** de la ressource dans l'état : la renommer revient à détruire puis
recréer l'objet, sauf bloc `moved`. Et **`terraform_data`** n'appartient à aucun
provider : c'est une ressource intégrée qui offre le cycle de vie complet
(`input`, `triggers_replace`, l'attribut calculé `output`).

Après `terraform init` et `terraform apply`, un plan à vide ne propose rien :

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq -c '[.resource_changes[] | {a: .address, ops: .change.actions}]'
```

```json
[{"a":"local_file.paquet","ops":["no-op"]},{"a":"random_pet.serie","ops":["no-op"]},{"a":"terraform_data.jeton","ops":["no-op"]}]
```

## Mettre à jour en place

Changez le **niveau**. L'argument `input` du jeton change, mais rien n'impose de
recréer la ressource : Terraform la met à jour en place.

```bash
terraform plan -var 'niveau=stable' -out=tfplan
terraform show -json tfplan | jq -c '.resource_changes[] | select(.address=="terraform_data.jeton") | .change.actions'
```

```text
["update"]
```

`["update"]` : l'objet est modifié, il n'est pas recréé. C'est le cas le moins
coûteux, et souvent le résultat attendu.

## Remplacer, et l'ordre du remplacement

Changez maintenant le **cycle**. Les `keepers` de `random_pet.serie` en
dépendent, donc la série est **remplacée**, son id change, et l'effet se propage.

```bash
terraform plan -var 'cycle=2' -out=tfplan
terraform show -json tfplan | jq -c '.resource_changes[] | {a: .address, ops: .change.actions}'
```

```json
{"a":"random_pet.serie","ops":["create","delete"]}
{"a":"local_file.paquet","ops":["create","delete"]}
{"a":"terraform_data.jeton","ops":["delete","create"]}
```

Trois remplacements, mais **deux ordres différents**, et c'est tout l'intérêt :

- `local_file.paquet` porte `create_before_destroy`, d'où `["create", "delete"]` :
  le nouveau fichier existe avant que l'ancien parte, sans fenêtre de trou.
- `random_pet.serie`, dont le paquet dépend, **hérite** de la règle par
  propagation : il passe lui aussi en `["create", "delete"]`, alors que rien
  n'est écrit dessus.
- `terraform_data.jeton`, qui n'est la dépendance de personne portant la règle,
  garde l'ordre par défaut `["delete", "create"]` : il détruit avant de créer.

C'est `triggers_replace` qui a déclenché le remplacement du jeton : il vaut l'id
de la série, qui vient de changer.

## Détruire

Un plan de destruction montre la dernière opération :

```bash
terraform plan -destroy -out=tfplan
terraform show -json tfplan | jq -c '.resource_changes[] | select(.address=="local_file.paquet") | .change.actions'
```

```text
["delete"]
```

## À vous de jouer

Vous savez lire dans le plan si une ressource sera mise à jour, remplacée, ou
détruite. Le challenge vous fait construire une configuration où ces opérations
se déclenchent à la demande, et les tests vérifient chaque signature.

```bash
dsoxlab run write-code-declare-resources
dsoxlab check write-code-declare-resources
dsoxlab hint write-code-declare-resources
```

Sous-objectif d'examen visé : **1c** (Terraform Authoring and Operations
Professional).

Référence : [Déclarer des ressources Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/declarer-ressources/)
