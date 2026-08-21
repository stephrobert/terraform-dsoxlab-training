# depends_on : le dernier recours, pas le réflexe

Terraform ordonne les ressources tout seul, à partir des **références** que vous
écrivez. `depends_on` sert uniquement pour la poignée de cas qu'aucune référence
ne peut exprimer. Le poser par confort, en double d'une référence déjà présente,
n'ordonne rien de plus et abîme le plan. Ce tutoriel montre où passe la
frontière, sur un exemple **jetable** réseau/serveur, avant que le challenge ne
vous fasse trancher bloc par bloc.

Tout tourne sur les providers `local` et `null`, en local.

## Une référence crée déjà une dépendance

Quand une ressource **référence** un attribut d'une autre, Terraform en déduit
l'ordre. Ici, le serveur cite le nom du réseau :

```hcl
resource "local_file" "reseau" {
  filename = "reseau.txt"
  content  = "cidr 10.0.0.0/24"
}

resource "local_file" "serveur" {
  filename = "serveur.txt"
  content  = "rattache a : ${local_file.reseau.filename}"
}
```

Le plan JSON expose cette dépendance. La section `configuration` liste les
références de chaque expression :

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq '.configuration.root_module.resources[] | select(.address=="local_file.serveur") | .expressions.content.references'
```

```json
["local_file.reseau.filename", "local_file.reseau"]
```

Et le `serveur` n'a **aucun** `depends_on` :

```json
"ABSENT"
```

L'ordre est pourtant garanti. Ajouter `depends_on = [local_file.reseau]` ici ne
changerait rien à l'ordre, mais rendrait le plan plus conservateur. C'est le
`depends_on` de confort à ne jamais écrire.

## La référence attend la fin de l'amont, pas un nom

Une idée fausse circule : une référence n'attendrait que la connaissance d'une
valeur, pas la disponibilité réelle de la ressource. C'est inexact. **Une
référence attend que l'amont ait fini d'être appliqué.**

La preuve tient en un exemple où l'amont met du temps. La `base` attend deux
secondes avant d'écrire un marqueur ; l'`app` le lit, et déclare une dépendance
par `triggers` :

```hcl
resource "null_resource" "base" {
  provisioner "local-exec" {
    command = "sleep 2 && echo pret > marqueur.txt"
  }
}

resource "null_resource" "app" {
  triggers = { base = null_resource.base.id }

  provisioner "local-exec" {
    command = "cat marqueur.txt"
  }
}
```

```bash
terraform apply
```

L'apply réussit. Si la référence n'avait attendu qu'un « nom connu »,
`cat marqueur.txt` se serait exécuté avant que `base` ne l'écrive, et aurait
échoué. Le succès prouve que la référence a bien attendu la **fin** de `base`.

## Quand la référence ne suffit pas : depends_on

Il reste les cas où une ressource dépend du **comportement** d'une autre, sans
utiliser aucune de ses données. Un service qui prépare un état sur le disque,
par exemple, sans exposer d'attribut exploitable. Là, il n'y a rien à
référencer, et `depends_on` devient nécessaire :

```hcl
resource "null_resource" "service" {
  provisioner "local-exec" {
    command = "sleep 1 && touch pret.flag"
  }
}

resource "null_resource" "consommateur" {
  depends_on = [null_resource.service]

  provisioner "local-exec" {
    command = "test -f pret.flag"
  }
}
```

```bash
terraform apply
```

L'apply réussit : `pret.flag` existe quand `consommateur` le cherche. Sans le
`depends_on`, Terraform lancerait les deux en parallèle et la vérification
échouerait, faute de la moindre référence pour ordonner.

Le plan confirme la dépendance explicite :

```bash
terraform show -json tfplan | jq '.configuration.root_module.resources[] | select(.address=="null_resource.consommateur") | .depends_on'
```

```json
["null_resource.service"]
```

## Le critère qui tranche

La règle n'est pas « la ressource risque-t-elle de démarrer trop tôt ? » (une
référence gère déjà ce cas), mais :

> **La ressource utilise-t-elle une donnée de l'amont dans ses arguments ?**

- **Oui** : une référence suffit, et elle est préférable. Pas de `depends_on`.
- **Non**, et la dépendance existe quand même (comportement, effet de bord) :
  alors, et seulement alors, `depends_on`.

La documentation le résume : « You should only use `depends_on` as a last resort
because it can cause Terraform to create more conservative plans that replace
more resources than necessary. »

## Une alternative : replace_triggered_by

Quand le besoin n'est pas d'ordonner mais de **remplacer** une ressource dès
qu'une autre change, `depends_on` n'est pas le bon outil : c'est
`replace_triggered_by`, dans le bloc `lifecycle`. Le sujet est traité dans
[le bloc lifecycle Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/lifecycle-terraform/).

## À vous de jouer

Vous savez distinguer une dépendance déjà exprimée par une référence d'une
dépendance réellement cachée. Le challenge vous fait nettoyer une configuration
qui mélange les deux : un `depends_on` redondant à retirer, un chemin en dur à
remplacer par une référence, et le seul `depends_on` légitime à poser.

```bash
dsoxlab run write-code-depends-on
dsoxlab check write-code-depends-on
dsoxlab hint write-code-depends-on
```

Sous-objectif d'examen visé : **2d** (Terraform Authoring and Operations
Professional).

Référence : [depends_on en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/depends-on/)
