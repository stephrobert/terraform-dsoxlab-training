# Writing a module you can call more than once

A Terraform module is a **directory of `.tf` files**, nothing more. Your project
already is one: it is the **root module**. Writing a child module is therefore
mostly about deciding what it **receives**, what it **exposes**, and what it
leaves to its caller.

That last point decides whether your module is reusable, and it fits in one
sentence from the documentation: **a module intended to be called by other
modules must not contain any `provider` block**. This tutorial shows why, on a
throwaway configuration.

## A minimal module

A module boils down to a directory, input variables, resources, and outputs:

```hcl
# modules/compteur/main.tf
terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

variable "libelle" {
  description = "Libelle du compteur, sert de nom de fichier."
  type        = string
}

resource "random_integer" "tirage" {
  min = 1
  max = 99
}

resource "local_file" "releve" {
  filename = "${path.root}/releves/${var.libelle}.txt"
  content  = "${var.libelle} : ${random_integer.tirage.result}\n"
}

output "valeur" {
  description = "Valeur tiree pour ce compteur."
  value       = random_integer.tirage.result
}
```

Note the `required_providers` block **inside the module**: a module always
declares which providers it needs. It does not **configure** them, and that
nuance is the heart of this lab.

## Calling it from the root

```hcl
module "compteur" {
  source = "./modules/compteur"

  libelle = "atelier"
}

output "valeur_atelier" {
  value = module.compteur.valeur
}
```

`terraform init` installs the module the way it installs a provider, and says so:

```text
Initializing modules...
- compteur in modules/compteur
```

The `apply` prefixes addresses with `module.<label>.`:

```text
module.compteur.random_integer.tirage: Creation complete after 0s [id=56]
module.compteur.local_file.releve: Creation complete after 0s [id=61a2097a...]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

valeur_atelier = 56
```

**An output is the only thing a module makes visible.** Without the
`output "valeur"` block, the caller could not read
`random_integer.tirage.result`: a module's resources are opaque to it.

## Calling it several times, with a single block

The common reflex is to duplicate the `module` block. The documentation
recommends the opposite: "You can configure Terraform to provision multiple
instances of the same module resources in **one** `module` block, **instead of
adding multiple blocks**".

```hcl
variable "ateliers" {
  type    = set(string)
  default = ["nord", "sud"]
}

module "compteur" {
  source   = "./modules/compteur"
  for_each = var.ateliers

  libelle = each.key
}

output "valeurs" {
  value = { for nom, instance in module.compteur : nom => instance.valeur }
}
```

Addresses then carry the key, and `module.compteur` becomes a **map** you walk:

```text
module.compteur["nord"].local_file.releve
module.compteur["nord"].random_integer.tirage
module.compteur["sud"].local_file.releve
module.compteur["sud"].random_integer.tirage
```

```text
valeurs = {
  "nord" = 17
  "sud" = 24
}
```

## Where a module stops being reusable

Now add a **provider configuration** inside the child module, as found in many
inherited modules:

```hcl
# modules/compteur/main.tf
provider "tls" {
  proxy {
    url = "http://proxy.interne.lan:3128"
  }
}
```

The `init` refuses, and its message already carries the fix:

```text
Error: Module is incompatible with count, for_each, and depends_on

The module at module.compteur is a legacy module which contains its own local
provider configurations, and so calls to it may not use the count, for_each,
or depends_on arguments.

If you also control the module "./modules/compteur", consider updating this
module to instead expect provider configurations to be passed by its caller.
```

Terraform calls such a module **legacy**, and the reason is structural: it cannot
instantiate several copies of a module that configures its own providers, because
it would not know how many configurations to create nor in which order to destroy
them.

One detail is worth knowing, it saves half an hour of puzzlement: this refusal
only triggers when the provider takes a **real configuration**. With `local`,
`random` or `null`, which accept no argument, Terraform merely warns,
`Redundant empty provider block`, and lets it through.

## What the module expects, what the caller hands over

Provider **configurations** are inherited by child modules; source and version
**requirements** never are. A module therefore keeps its `required_providers` and
loses its `provider` blocks.

Inheritance has a limit: it only passes the **default** configuration. For a
module to use an **aliased** one, it must declare it:

```hcl
# modules/compteur/versions.tf
terraform {
  required_providers {
    local = {
      source                = "hashicorp/local"
      version               = ">= 2.5"
      configuration_aliases = [local.secondaire]
    }
  }
}
```

Without that line, a module resource writing `provider = local.secondaire` fails
on `Provider configuration not present`. With it, but with nothing on the caller
side, the failure becomes `Missing required provider configuration`: the module
asks for what nobody gives it. The caller closes the loop:

```hcl
module "compteur" {
  source   = "./modules/compteur"
  for_each = var.ateliers

  providers = {
    local.secondaire = local.archivage
  }

  libelle = each.key
}
```

On the left the name **the child expects**, on the right the **root**
configuration. Other providers stay inherited without writing anything: measured,
a partial `providers` does not cancel inheritance for the ones it does not name.

## A reservation the documentation states and few people read

Not everything deserves a module. The official docs are explicit: "We **do not**
recommend writing modules that are just thin wrappers around single other
resource types. If you have trouble finding a name for your module that isn't the
same as the main resource type inside it, that may be a sign that your module is
not creating any new abstraction". A `reseau` module holding a single
`..._network` resource factors nothing out: use the resource directly.

## Your turn

You can write a module, call it, read its outputs, instantiate it several times
with a single block, and above all recognise what would make it unusable: a
provider configuration in the child. The challenge hands you a project whose
inherited module carries exactly that flaw, and whose `init` fails before the
first plan.

```bash
dsoxlab run modules-create-modules
dsoxlab check modules-create-modules
dsoxlab hint modules-create-modules
```

Target exam sub-objective: **4a** (write and use modules), Associate and
Professional level.

Reference: [creating modules](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/creation-modules/)
