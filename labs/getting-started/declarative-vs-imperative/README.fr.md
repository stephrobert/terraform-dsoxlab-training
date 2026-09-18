# Déclaratif contre impératif : la convergence se prouve

« Terraform est déclaratif » est une phrase qu'on répète sans la vérifier. Elle
ne veut pas dire que le code est plus joli, ni qu'il y a moins de lignes. Elle
décrit une **propriété mesurable** : appliquer deux fois donne le même résultat
qu'appliquer une fois. Ce tutoriel montre où un script perd cette propriété, et
comment la prouver sans y croire sur parole.

## Le script n'est pas fautif étape par étape

Prenez ce script, qui fabrique un rapport avec un identifiant :

```bash
mkdir -p "$SORTIE"
IDENTIFIANT="$(tr -dc 'a-z0-9' < /dev/urandom | head -c 8)"
printf 'rapport genere, identifiant : %s\n' "$IDENTIFIANT" >> "$SORTIE/rapport.txt"
```

Chaque ligne est raisonnable. `mkdir -p` est même explicitement idempotent. Le
défaut n'est dans aucune d'elles : il est que **le résultat dépend du nombre
d'exécutions**. Deux appels donnent deux identifiants, et un rapport à deux
lignes. Dix appels en donnent dix.

C'est le trait commun de l'impératif : on décrit *comment faire*, et faire deux
fois n'est pas faire une fois.

## Décrire un état, c'est renoncer à décrire les étapes

La même intention, exprimée en Terraform :

```hcl
resource "random_string" "identifiant" {
  length  = 8
  special = false
  upper   = false

  keepers = {
    projet = "declaratif"
  }
}

resource "local_file" "rapport" {
  content  = "rapport genere, identifiant : ${random_string.identifiant.result}\n"
  filename = "${path.module}/sortie-declarative/rapport.txt"
}
```

Rien ici ne dit « tire un identifiant ». Le texte dit : *il existe un identifiant
de huit caractères, et un fichier dont le contenu le porte*. Terraform compare
cette description au state, et n'agit que sur l'écart.

## keepers : ce qui autorise un nouveau tirage

Une valeur aléatoire pose une question évidente : pourquoi ne change-t-elle pas
à chaque `apply` ? Parce qu'elle est **mémorisée dans le state**, et que le
provider ne la retire que si **`keepers`** change.

```hcl
keepers = {
  projet = "declaratif"   # fixe : l'identifiant ne sera jamais retiré
}
```

```hcl
keepers = {
  version = var.version_du_rapport   # change avec la variable : nouveau tirage
}
```

C'est la commande que vous gardez sur l'aléatoire. Le script, lui, n'en a
aucune : `/dev/urandom` ne se souvient de rien.

## triggers : dépendre de ce qu'il faut

`null_resource` accepte un bloc **`triggers`**, une carte de valeurs dont le
changement provoque son **remplacement** :

```hcl
resource "null_resource" "empreinte" {
  triggers = {
    identifiant = random_string.identifiant.result
  }
}
```

Elle sera remplacée si l'identifiant change, et **seulement** dans ce cas. C'est
la même logique que `keepers`, appliquée à une action plutôt qu'à une valeur.

## L'idempotence se lit dans un code retour

Ne jugez jamais un plan à l'œil. La commande répond par un code :

```bash
terraform plan -detailed-exitcode ; echo $?
```

| Code | Signification |
|---|---|
| `0` | aucun changement |
| `1` | erreur |
| `2` | des changements sont prévus |

Juste après un `apply`, ce code doit valoir `0`. C'est la preuve machine de la
convergence, et elle ne dépend d'aucune tournure de phrase.

## La dérive, et ce qu'elle n'emporte pas

Supprimez le rapport hors de Terraform :

```bash
rm sortie-declarative/rapport.txt
terraform plan -detailed-exitcode ; echo $?   # 2
```

Enregistrez le plan et lisez-le en JSON :

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.resource_changes[] | select(.change.actions != ["no-op"]) | {address, actions: .change.actions}'
```

```text
{"address": "local_file.rapport", "actions": ["create"]}
```

**Une seule création.** L'identifiant n'est pas retiré, la `null_resource` n'est
pas remplacée. La réparation se fait par un `apply`, **sans toucher au code**, et
l'identifiant d'avant la dérive est toujours là.

<Aside type="caution" title="Une correction manuelle n'est pas une convergence">
Recréer le fichier à la main donnerait un rapport au bon endroit, et laisserait
le state en désaccord avec la réalité au premier détail près. C'est l'outil qui
répare, pas vous : c'est tout l'intérêt d'avoir décrit un état.
</Aside>

## À vous de jouer

Vous savez maintenant qu'un script impératif diverge parce que son résultat
dépend du nombre d'exécutions, qu'une configuration décrit un état que Terraform
compare au state, que `keepers` et `triggers` sont vos prises sur l'aléatoire et
sur les remplacements, que l'idempotence se lit dans un code retour, et qu'une
dérive se répare là où elle a eu lieu.

Le challenge vous fait traduire le script fourni, puis produire ces preuves.

```bash
dsoxlab run getting-started-declarative-vs-imperative
dsoxlab check getting-started-declarative-vs-imperative
dsoxlab hint getting-started-declarative-vs-imperative
```

Sous-objectif d'examen visé : **1b** (`plan` : prouver l'idempotence, détecter
une dérive et la corriger).

Référence : [Déclaratif contre impératif](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/declaratif-vs-imperatif/)
