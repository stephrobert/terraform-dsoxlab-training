# Diagnostiquer une dérive, adopter une orpheline

Deux situations différentes mènent au même symptôme, un plan qui propose des
changements alors que personne n'a touché au code. Dans la première, **l'objet
réel a changé** hors de Terraform : c'est une **dérive**. Dans la seconde, un
objet existe mais **n'a jamais été dans le state** : c'est une **orpheline**.

Les deux se réparent avec des outils distincts, et les confondre coûte cher : on
ne répare pas une dérive avec un `import`, et on ne récupère pas une orpheline
avec un `refresh`.

## Le terrain d'essai

Dans un répertoire à part, hors du challenge :

```hcl
terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

resource "local_file" "bulletin" {
  filename = "${path.root}/sortie/bulletin.txt"
  content  = "bulletin du jour\n"
}
```

Un `terraform init` puis un `terraform apply` créent le fichier. Simulez ensuite
l'incident que tout le monde a déjà vécu, la correction faite directement sur le
serveur :

```bash
echo "corrige a la main" > sortie/bulletin.txt
```

## Le plan ordinaire mélange deux informations

Terraform veut recréer le fichier. C'est exact, mais insuffisant pour un
diagnostic : le plan ne dit pas si le problème vient du **réel** qui a bougé ou
du **code** qui a changé. Le JSON le montre bien, l'information est rangée
**deux fois** :

```bash
terraform plan -out=ordinaire.tfplan
terraform show -json ordinaire.tfplan | jq '{
  drift: [.resource_drift[]?.address],
  changes: [.resource_changes[]?.address]
}'
```

```json
{
  "drift": ["local_file.bulletin"],
  "changes": ["local_file.bulletin"]
}
```

## `plan -refresh-only` isole la dérive

Le mode **refresh-only** ne propose aucune modification de l'infrastructure : il
décrit seulement le **rattrapage du state**. La différence se lit dans le JSON,
où `resource_changes` est désormais **vide** :

```bash
terraform plan -refresh-only -out=derive.tfplan
terraform show -json derive.tfplan > derive-plan.json
jq '{drift: [.resource_drift[]?.address], changes: [.resource_changes[]?.address]}' derive-plan.json
```

```json
{
  "drift": ["local_file.bulletin"],
  "changes": []
}
```

**Cette absence est la signature du diagnostic.** Un fichier de plan étant un
**binaire**, la conversion en JSON n'est pas cosmétique : c'est elle qui rend la
dérive lisible en revue, archivable, et vérifiable par un script.

## Deux codes de sortie qui ne disent pas la même chose

`-detailed-exitcode` rend **0** sans changement, **2** avec, **1** en cas
d'erreur. Appliqué aux deux formes de plan, il devient un outil de diagnostic à
part entière :

| Commande | Ce que le code 2 signifie |
| --- | --- |
| `terraform plan -detailed-exitcode` | le **réel** ne correspond pas au **code** |
| `terraform plan -refresh-only -detailed-exitcode` | le **state** ne correspond pas au **réel** |

C'est la distinction que l'on manque le plus souvent. Après un
`terraform apply -refresh-only`, qui **inscrit la dérive dans le state**, le
refresh-only rend **0** alors que le plan ordinaire rend encore **2** : le state
dit désormais la vérité, mais cette vérité ne correspond toujours pas au code.
Un `apply` ordinaire remet ensuite l'objet en conformité, et les deux codes
tombent à **0** ensemble.

## Adopter une ressource qui n'a jamais été gérée

Le bloc **`import`**, déclaratif depuis Terraform **1.5**, rattache un objet
existant à une adresse du state. Deux attributs suffisent, l'adresse visée et
l'identifiant de l'objet chez le provider :

```hcl
resource "random_string" "credential" {
  length = 22
}

import {
  to = random_string.credential
  id = "V3ryS3cretL3gacyStr1ng"
}
```

Le plan annonce l'adoption, et le compteur porte une catégorie à part,
`to import` :

```text
  # random_string.credential will be imported
Plan: 1 to import, 0 to add, 0 to change, 0 to destroy.
```

Côté JSON, l'entrée porte `"actions": ["no-op"]` et un champ `importing` : rien
n'est créé ni détruit, l'objet change simplement de statut.

## Le piège de l'import : les attributs qui ne collent pas

Voici ce qui transforme une adoption en perte. Si la **configuration** décrit des
attributs que l'objet importé **ne porte pas**, Terraform ne se contente pas
d'adopter, il **remplace**. Déclarez `length = 32` pour une chaîne qui en fait
22 :

```text
  # random_string.credential must be replaced
  # (imported from "V3ryS3cretL3gacyStr1ng")
  # Warning: this will destroy the imported resource
      ~ length      = 22 -> 32 # forces replacement
      ~ result      = "V3ryS3cretL3gacyStr1ng" -> (known after apply)
Plan: 1 to import, 1 to add, 0 to change, 1 to destroy.
```

L'avertissement est explicite, **`this will destroy the imported resource`**, et
le JSON le confirme par `"actions": ["delete", "create"]` avec
`"replace_paths": [["length"]]`. Mais il n'apparaît qu'**au plan** : un
`apply -auto-approve` lancé sans lire emporte la valeur, et le plan **suivant**
annonce paisiblement `No changes`. La perte devient alors indétectable.

Quand la valeur héritée doit survivre telle quelle, le garde-fou est
`ignore_changes` :

```hcl
resource "random_string" "credential" {
  length = 32

  lifecycle {
    ignore_changes = all
  }
}
```

L'objet est adopté **tel qu'il est**, sans que Terraform cherche à l'aligner sur
une configuration écrite pour les objets à venir.

## Lequel employer, et quand

| Symptôme | Diagnostic | Réparation |
| --- | --- | --- |
| Le plan veut recréer un objet qui existe | dérive, ou orpheline | `plan -refresh-only` pour trancher |
| `resource_drift` non vide | **dérive** : le réel a changé | `apply -refresh-only`, puis `apply` |
| L'objet n'est dans aucun state | **orpheline** | bloc `import` |
| L'import annonce `must be replaced` | attributs divergents | `ignore_changes`, ou aligner le code |

## À vous de jouer

Vous savez isoler une dérive avec un plan refresh-only, lire la différence entre
`resource_drift` et `resource_changes`, distinguer ce que disent les deux
`-detailed-exitcode`, adopter une ressource préexistante par un bloc `import`,
et reconnaître au plan l'adoption qui va détruire ce qu'elle prétend reprendre.
Le challenge vous confie un fichier bricolé à la main et un jeton hérité qu'un
service tiers connaît, donc impossible à regénérer.

```bash
dsoxlab run state-diagnose-state
dsoxlab check state-diagnose-state
dsoxlab hint state-diagnose-state
```

Sous-objectif d'examen visé : **1e** (gérer le state), niveau Associate et
Professional.

Référence : [diagnostiquer le state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/diagnostiquer-state/)
