# Léguer une infrastructure, plutôt que la détruire

Un lot de ressources arrive en fin de cycle. Certaines doivent **disparaître**,
d'autres doivent **survivre** sous la responsabilité de quelqu'un d'autre. Les
deux intentions passent par le même bloc, `removed`, et se distinguent par un
seul argument. Se tromper d'argument ne provoque aucune erreur : cela supprime
l'infrastructure.

Ce tutoriel monte le mécanisme sur une configuration jetable, puis va jusqu'à
ses frontières : ce qu'il fait d'un `for_each`, ce qu'il refuse de faire, et ce
qu'il permet que la ligne de commande ne permet pas.

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

resource "local_file" "inventaire" {
  filename = "${path.root}/inventaire.csv"
  content  = "ref,qte\nvis-8,120\n"
}

resource "local_file" "capteurs" {
  for_each = toset(["nord", "sud"])
  filename = "${path.root}/capteur-${each.key}.txt"
  content  = "capteur ${each.key}\n"
}

resource "random_pet" "demo" {
  length = 2
}

module "legs" {
  source = "./modules/legs"
}
```

Le module `./modules/legs` tient en une ressource, `random_pet.interne`. Après
`terraform init` puis `terraform apply`, le state porte cinq objets :

```text
local_file.capteurs["nord"]
local_file.capteurs["sud"]
local_file.inventaire
random_pet.demo
module.legs.random_pet.interne
```

## Un bloc, deux intentions opposées

Le bloc `removed` déclare qu'une ressource **n'est plus gérée**. Son argument
`destroy`, dans un bloc `lifecycle`, décide du sort de l'objet réel :

```hcl
removed {
  from = local_file.capteurs

  lifecycle {
    destroy = false
  }
}
```

Deux règles gouvernent son écriture. D'abord, `from` prend une **référence sans
guillemets**, comme dans un bloc `moved`. Ensuite, le bloc `resource`
correspondant doit avoir **disparu** de la configuration : les deux ne
coexistent jamais, et Terraform refuse de planifier tant que c'est le cas, avec
`Removed resource still exists`.

Ce qui compte vraiment tient dans l'argument `destroy`, et le tableau se lit
dans le mauvais sens si on suppose que « removed » signifie « retiré du
state » :

| Écriture | Action planifiée | L'objet réel |
| --- | --- | --- |
| sans bloc `lifecycle` | `delete` | **détruit** |
| `lifecycle { destroy = true }` | `delete` | **détruit** |
| `lifecycle { destroy = false }` | `forget` | conservé |

**Le défaut est donc la destruction.** Aucun avertissement ne le signale au
moment d'écrire le bloc : c'est le plan, et lui seul, qui le dit.

## Un bloc pour toute une ressource, une action par instance

Sur une ressource multipliée par `for_each` ou `count`, un seul bloc suffit, et
le plan détaille instance par instance :

```text
 # local_file.capteurs["nord"] will no longer be managed by Terraform, but will not be destroyed
 # local_file.capteurs["sud"] will no longer be managed by Terraform, but will not be destroyed

Plan: 0 to add, 0 to change, 0 to destroy.
```

Le JSON du plan confirme, avec une action par instance :

```json
[
  { "address": "local_file.capteurs[\"nord\"]", "actions": ["forget"] },
  { "address": "local_file.capteurs[\"sud\"]",  "actions": ["forget"] }
]
```

Après l'`apply`, `capteur-nord.txt` et `capteur-sud.txt` sont toujours sur le
disque, et les deux adresses ont quitté le state. Notez la ligne de synthèse :
`0 to destroy`, alors que deux objets sortent de la gestion. **Les `forget` ne
sont pas comptés comme des destructions**, ce qui est logique, mais rend le
compteur trompeur si on le lit seul.

## Ce que le bloc refuse : une instance précise

Le grain le plus fin du bloc est la **ressource entière**. Viser une seule
instance échoue :

```text
Error: Resource instance keys not allowed

Resource address must be a resource (e.g. "test_instance.foo"), not a
resource instance (e.g. "test_instance.foo[1]").
```

Pour sortir une seule clé, il faut la commande, qui elle accepte l'adresse
indexée :

```bash
terraform state rm 'local_file.capteurs["nord"]'
```

Et là se cache le vrai piège, qui n'a rien à voir avec le state : tant que la
clé reste dans le `for_each`, la configuration **redemande** l'objet. Le plan
suivant le recrée, et le fichier que vous vouliez léguer est écrasé :

```text
  # local_file.capteurs["nord"] will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

Retirer la clé de la collection fait taire le plan : `No changes. Your
infrastructure matches the configuration.` **Un retrait d'instance se fait donc
en deux gestes**, la commande puis l'alignement du code, jamais un seul.

## Ce que le bloc permet et que la commande ne fait pas simplement

Un `removed` accepte un **module entier**, et rend un `forget` par ressource
qu'il contient :

```hcl
removed {
  from = module.legs

  lifecycle {
    destroy = false
  }
}
```

```text
 # module.legs.random_pet.interne will no longer be managed by Terraform, but will not be destroyed
```

C'est la façon propre de faire migrer un module vers un autre dépôt : une seule
déclaration, relue en revue, quel que soit le nombre de ressources dedans.

## Débrancher proprement : les provisioners de destruction

Un objet légué a parfois besoin d'être **désenregistré** avant de partir : sortir
d'un inventaire, d'un annuaire, d'une supervision. Le bloc `removed` accepte
pour cela des provisioners, et l'attribut `self` y désigne la ressource
concernée :

```hcl
removed {
  from = local_file.inventaire

  lifecycle {
    destroy = true
  }

  provisioner "local-exec" {
    when    = destroy
    command = "echo desenregistrement ${self.filename} >> journal-migration.txt"
  }
}
```

À l'`apply`, le provisioner s'exécute avant la destruction :

```text
local_file.inventaire: Provisioning with 'local-exec'...
local_file.inventaire (local-exec): Executing: ["/bin/sh" "-c" "echo desenregistrement ./inventaire.csv >> journal-migration.txt"]
local_file.inventaire: Destruction complete after 0s
```

**Seuls les provisioners de destruction sont acceptés** dans un bloc `removed`,
et l'oubli de `when` est refusé sans ambiguïté :

```text
Error: Invalid provisioner block

Only destroy-time provisioners are valid in "removed" blocks. To declare a
destroy-time provisioner, use:
    when = destroy
```

## Le bloc s'écrit avant de s'appliquer

C'est l'argument décisif face à `terraform state rm`, et il n'a rien à voir avec
la syntaxe. Un bloc `removed` écrit et poussé en revue **décrit une opération
qui n'a pas encore eu lieu** : `terraform plan` la montre, la revue de code la
discute, l'`apply` la joue plus tard. Tant qu'il n'est pas appliqué,
`terraform plan -detailed-exitcode` sort en **code 2**, ce qui signale un
changement en attente.

Une commande impérative, elle, n'existe qu'au moment où quelqu'un la tape sur son
poste : rien à relire, rien à discuter, aucune trace dans le dépôt.

## À vous de jouer

Vous savez qu'un bloc `removed` détruit par défaut, que `destroy = false` change
l'action en `forget`, qu'un seul bloc couvre toutes les instances d'un
`for_each`, qu'une clé précise passe obligatoirement par `terraform state rm`
suivi d'un alignement de la collection, qu'un module entier se lègue en une
déclaration, et qu'un provisioner de destruction permet de débrancher un objet
avant de le lâcher. Le challenge vous confie un lot d'artefacts en fin de vie,
avec pour chacun une décision différente à prendre.

```bash
dsoxlab run state-removed-block
dsoxlab check state-removed-block
dsoxlab hint state-removed-block
```

Sous-objectifs d'examen visés : **1e** (gérer le state) et **4c** (refactorer une
configuration), niveau Professional.

Référence : [le bloc removed](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/bloc-removed/)
