# Placer chaque garde-fou au bon niveau

Terraform offre **quatre** mécanismes pour refuser une valeur absurde, et le
piège n'est pas d'écrire une condition : c'est de la placer au bon endroit. Un
bloc `validation`, une `precondition`, une `postcondition` et un bloc `check` ne
s'évaluent pas au même moment et ne bloquent pas la même chose.

Ce tutoriel les construit un par un sur un exemple **jetable** : un bon de
commande qui calcule un total et le refuse s'il est absurde. Le challenge, lui,
vous fera transposer ces quatre outils à un autre cas. Le lab tourne sur le seul
provider `local`.

## Monter l'exemple

Dans un répertoire à part, un `main.tf` qui déclare une région, une quantité, et
un reçu :

```hcl
variable "region" {
  type    = string
  default = "eu-ouest"
}

variable "quantite" {
  type    = number
  default = 10
}

locals {
  total = var.quantite * 10
}

resource "local_file" "recu" {
  filename = "${path.module}/recu.json"
  content  = jsonencode({ region = var.region, quantite = var.quantite, total = local.total })
}
```

Lancez `terraform init`. Vous ajouterez chaque garde-fou au fil des sections.

## validation : filtrer une variable d'entrée

Le mécanisme le plus simple vit sur la variable elle-même, et refuse la valeur
**avant même** que le plan ne soit généré. Ajoutez un bloc `validation` à
`region` :

```hcl
variable "region" {
  type    = string
  default = "eu-ouest"

  validation {
    condition     = contains(["eu-ouest", "eu-nord", "us-est"], var.region)
    error_message = "region inconnue."
  }
}
```

```bash
terraform plan -var 'region=lune'
```

```text
Error: Invalid value for variable

  on main.tf line 1:
```

Le plan s'arrête net. Point clé : une `validation` **ne voit que sa propre
variable**. Elle ne peut rien dire d'un `local` ni du résultat d'une ressource.

## Une validation qui regarde une autre variable

Depuis Terraform 1.9, une `validation` peut référencer **une autre variable**.
Ajoutez une option express, valable seulement dans une région :

```hcl
variable "express" {
  type    = bool
  default = false

  validation {
    condition     = !var.express || var.region == "eu-ouest"
    error_message = "l'option express n'existe qu'en eu-ouest."
  }
}
```

La condition se lit « pas d'express, **ou** région eu-ouest ». Testez les deux
cas :

```bash
terraform plan -var 'express=true' -var 'region=us-est'
```

```text
Error: Invalid value for variable

  on main.tf line 16:
```

```bash
terraform plan -var 'express=true' -var 'region=eu-ouest'
```

Ce second plan passe. La règle ne se déclenche que dans la combinaison visée.

## precondition : contrôler avant l'action

Certaines vérifications portent sur une valeur calculée, hors de portée d'une
`validation`. La `precondition` vit dans le bloc `lifecycle` de la ressource et
s'évalue **avant** de l'écrire. Exigez une quantité d'au moins 1 :

```hcl
resource "local_file" "recu" {
  filename = "${path.module}/recu.json"
  content  = jsonencode({ region = var.region, quantite = var.quantite, total = local.total })

  lifecycle {
    precondition {
      condition     = var.quantite >= 1
      error_message = "quantite doit valoir au moins 1."
    }
  }
}
```

```bash
terraform plan -var 'quantite=0'
```

```text
Error: Resource precondition failed

  on main.tf line 36, in resource "local_file" "recu":
```

La précondition bloque avant que le fichier ne soit écrit.

## postcondition : vérifier le résultat réel

Une `postcondition` s'évalue **après** l'action et voit l'objet produit via
`self`. Ajoutez-la sous la précondition pour garantir que le reçu porte bien un
total :

```hcl
    postcondition {
      condition     = can(jsondecode(self.content).total)
      error_message = "le recu ne porte pas de total."
    }
```

C'est le seul mécanisme qui dispose de `self`. Une `validation` ou une
`precondition` ne peuvent pas relire un résultat qui n'existe pas encore au
moment où elles s'évaluent.

## check : avertir sans bloquer

Les quatre premiers mécanismes **arrêtent** Terraform. Parfois, on veut
seulement un signal. Le bloc `check` s'écrit **au niveau racine**, jamais dans
une ressource :

```hcl
check "quota_mensuel" {
  assert {
    condition     = local.total <= 1000
    error_message = "quota mensuel depasse."
  }
}
```

Poussez la quantité au-delà du quota et appliquez :

```bash
terraform apply -var 'quantite=120'
```

```text
Warning: Check block assertion failed

  on main.tf line 48, in check "quota_mensuel":

Apply complete! Resources: 1 added, 0 changed, 1 destroyed.
```

C'est un **Warning**, pas une **Error**, et l'apply se termine. Un `check`
observe et signale, il ne garde pas la porte.

## Lire où chaque garde a été posé

Le plan JSON expose un tableau `checks` dont le champ `kind` prouve le **niveau**
de chaque contrôle :

```bash
terraform show -json | jq -c '.checks[] | {kind: .address.kind, addr: .address.to_display, status}'
```

```text
{"kind":"check","addr":"check.quota_mensuel","status":"fail"}
{"kind":"resource","addr":"local_file.recu","status":"pass"}
{"kind":"var","addr":"var.express","status":"pass"}
{"kind":"var","addr":"var.region","status":"pass"}
```

`kind: var` pour les validations, `kind: resource` pour la précondition et la
postcondition, `kind: check` pour le bloc. Et `quota_mensuel` est en `fail`
alors que l'apply a réussi : la preuve, dans les données, qu'un `check` ne bloque
pas.

## À vous de jouer

Vous savez distinguer les quatre garde-fous par leur niveau et leur effet. Le
challenge applique tout cela à un autre décor, et les tests vérifient le `kind`
de chaque contrôle que vous posez :

```bash
dsoxlab run write-code-conditionals
dsoxlab check write-code-conditionals
dsoxlab hint write-code-conditionals
```

| Mécanisme | Porte sur | S'évalue | En cas d'échec | `kind` |
|---|---|---|---|---|
| `validation` | une variable d'entrée | avant le plan | arrête | `var` |
| `precondition` | toute expression, dont un `local` | avant l'action | arrête | `resource` |
| `postcondition` | le résultat réel, via `self` | après l'action | arrête | `resource` |
| bloc `check` | toute expression | à l'apply | **avertit seulement** | `check` |

Le choix ne dépend pas de la condition à écrire, mais de deux questions : **sur
quoi** porte le contrôle, et **doit-il bloquer** ?

Sous-objectif d'examen visé : **2a** (Terraform Authoring and Operations
Professional).

Référence : [Valider les entrées d'une configuration Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/conditions-terraform/)
