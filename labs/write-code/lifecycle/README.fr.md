# Le bloc lifecycle décide de l'ordre, pas vous

Le bloc `lifecycle` réordonne le graphe de dépendances de Terraform, se propage
dans un sens contre-intuitif, et refuse certaines valeurs qu'on croit légitimes.
Ce tutoriel pose ses règles une par une sur un exemple **jetable** : une chaîne
de build qui produit un artefact versionné. Le challenge, lui, vous fera
appliquer ces mêmes règles à un autre décor.

La preuve d'un comportement se lit toujours dans le tableau `actions` du plan
JSON : `["delete", "create"]` est l'ordre par défaut, `["create", "delete"]`
prouve qu'une règle l'a inversé. Tout tourne sur `local`, `random` et
`terraform_data`, sans cloud.

## Monter l'exemple

Dans un répertoire à part, un `main.tf` sans aucun bloc `lifecycle` pour partir
du comportement par défaut :

```hcl
variable "build" {
  type    = number
  default = 1
}

resource "random_pet" "empreinte" {
  length  = 2
  keepers = { build = var.build }
}

resource "local_file" "artefact" {
  filename = "${path.module}/out/artefact-${random_pet.empreinte.id}.txt"
  content  = "build=${var.build}\n"
}
```

Le nom de l'artefact dépend de l'empreinte, donc changer `build` force un
**remplacement**. Après `init` et `apply`, regardez l'ordre par défaut :

```bash
terraform plan -var 'build=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.address=="local_file.artefact") | .change.actions'
```

```text
["delete","create"]
```

Terraform **détruit avant de créer**. Il existe donc un instant où l'artefact
n'existe plus.

## create_before_destroy : supprimer la fenêtre de coupure

Ajoutez un bloc `lifecycle` à l'artefact :

```hcl
  lifecycle {
    create_before_destroy = true
  }
```

```bash
terraform apply -auto-approve
terraform plan -var 'build=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | {a: .address, actions: .change.actions}'
```

```text
{"a":"local_file.artefact","actions":["create","delete"]}
{"a":"random_pet.empreinte","actions":["create","delete"]}
```

L'artefact passe en `["create", "delete"]` : la fenêtre a disparu. Regardez la
deuxième ligne, c'est le piège central : `random_pet.empreinte` a basculé aussi,
alors que vous n'avez rien écrit dessus. La règle se propage vers les
**dépendances** de la ressource, pas vers ses dépendants. L'artefact dépend de
l'empreinte, donc pour créer le nouvel artefact d'abord, la nouvelle empreinte
doit exister d'abord. Si vous aviez posé la règle sur `random_pet.empreinte`,
l'artefact serait resté en `["delete", "create"]`.

## prevent_destroy : refuser un plan destructeur

Ajoutez une ressource protégée :

```hcl
resource "local_file" "archive" {
  filename = "${path.module}/out/archive.txt"
  content  = "donnees a conserver"

  lifecycle {
    prevent_destroy = true
  }
}
```

```bash
terraform apply -auto-approve
terraform plan -destroy
```

```text
Error: Instance cannot be destroyed

  on main.tf line 15:
  15: resource "local_file" "archive" {
```

Le plan échoue avant toute action. Attention à la limite, elle est essentielle :
cette protection ne tient que tant que le bloc `resource` existe. Supprimez les
lignes de `local_file.archive`, et Terraform détruira l'objet sans protester,
parce que la règle n'est pas enregistrée dans l'état. Pas de bloc, pas de
protection.

## ignore_changes : ignorer un attribut, pas la ressource

Une ressource dont un attribut est piloté ailleurs. Ici, on ignore le contenu
mais on garde le contrôle des permissions :

```hcl
variable "note" {
  type    = string
  default = "v1"
}

variable "droits" {
  type    = string
  default = "0644"
}

resource "local_file" "config" {
  filename        = "${path.module}/out/config.txt"
  content         = var.note
  file_permission = var.droits

  lifecycle {
    ignore_changes = [content]
  }
}
```

Notez la syntaxe : `[content]`, sans guillemets. Testez les deux attributs :

```bash
terraform apply -auto-approve
terraform plan -var 'note=v2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.address=="local_file.config") | .change.actions'
```

```text
["no-op"]
```

```bash
terraform plan -var 'droits=0600' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.address=="local_file.config") | .change.actions'
```

```text
["delete","create"]
```

Le changement de contenu est absorbé (`no-op`), celui de permissions passe. Si
vous aviez écrit `ignore_changes = all`, ce second plan serait vide aussi : vous
auriez aveuglé la ressource entière. Un piège de fond : `ignore_changes` compare
la **configuration à l'état**, pas au fichier réel. Modifier le fichier à la
main, hors de Terraform, ne serait pas absorbé.

## replace_triggered_by : remplacer depuis une valeur nue

Vous voulez qu'une ressource soit remplacée quand `build` change, sans qu'aucun
de ses attributs ne bouge. Premier réflexe, pointer la variable :

```hcl
lifecycle {
  replace_triggered_by = [var.build]
}
```

```bash
terraform validate
```

```text
Error: Invalid reference in replace_triggered_by expression
```

`replace_triggered_by` n'accepte que des **ressources gérées**, jamais une
variable ni un local. La parade est `terraform_data`, une ressource intégrée
sans provider qui porte la valeur et devient référençable :

```hcl
resource "terraform_data" "jeton" {
  input = var.build
}

resource "local_file" "sceau" {
  filename = "${path.module}/out/sceau.txt"
  content  = "sceau"

  lifecycle {
    replace_triggered_by = [terraform_data.jeton]
  }
}
```

```bash
terraform apply -auto-approve
terraform plan -var 'build=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.address=="local_file.sceau") | {actions: .change.actions, reason: .action_reason}'
```

```text
{"actions":["delete","create"],"reason":"replace_by_triggers"}
```

`action_reason: "replace_by_triggers"` est la signature exacte : c'est la seule
valeur qui prouve un `replace_triggered_by`. Une autre trahirait un remplacement
venu d'un changement d'attribut.

## precondition et postcondition

Deux contrôles vivent aussi dans le bloc `lifecycle`. La `precondition` vérifie
une hypothèse **avant** l'action ; la `postcondition` relit le résultat via
`self` **après**. Sur notre artefact, on pourrait exiger un build strictement
positif et un fichier non vide :

```hcl
  lifecycle {
    create_before_destroy = true

    precondition {
      condition     = var.build > 0
      error_message = "build doit etre strictement positif."
    }

    postcondition {
      condition     = length(self.content) > 0
      error_message = "L'artefact ecrit est vide."
    }
  }
```

`self` n'existe que dans une postcondition : c'est le seul mécanisme capable de
relire l'objet produit. Le sujet est creusé dans
[valider les entrées d'une configuration Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/conditions-terraform/).

## À vous de jouer

Vous savez lire l'ordre et la cause d'un remplacement dans le plan JSON. Le
challenge applique ces règles à un autre décor et vérifie chaque comportement :

```bash
dsoxlab run write-code-lifecycle
dsoxlab check write-code-lifecycle
dsoxlab hint write-code-lifecycle
```

| Règle | Effet | Le piège |
|---|---|---|
| `create_before_destroy` | créer avant détruire | se propage vers les **dépendances** |
| `prevent_destroy` | rejette le plan de destruction | contourné en supprimant le bloc |
| `ignore_changes` | ignore un attribut | compare config et état, pas le réel |
| `replace_triggered_by` | remplace sur mouvement d'une cible | refuse les variables : passer par `terraform_data` |
| `precondition` / `postcondition` | valident au plan | `self` seulement en postcondition |

Sous-objectif d'examen visé : **2d** (Terraform Authoring and Operations
Professional).

Référence : [Le bloc lifecycle Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/lifecycle-terraform/)
