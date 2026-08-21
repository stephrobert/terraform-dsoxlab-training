# A module that configures its provider is no longer composable

Three practices separate a **reusable** module from one that works once: it does
not configure its **provider**, it **receives** its dependencies, and it
**documents** itself. All three can be checked in the artefacts Terraform
produces, without reading a line of configuration.

## Why a module does not configure its provider

The reason is not comfort, it is the **lifecycle**. The documentation is blunt: "A
provider configuration must always stay present in the overall Terraform
configuration for longer than all of the resources it manages." A module carrying
**both** its resources and the configuration managing them disappears in one
piece, and destroying what it created cleanly becomes impossible.

Terraform also punishes the call, as soon as that `provider` block actually
**configures** something:

```text
Error: Module is incompatible with count, for_each, and depends_on

The module at module.cle is a legacy module which contains its own local
provider configurations, and so calls to it may not use the count, for_each,
or depends_on arguments.

If you also control the module "./mod", consider updating this module to
instead expect provider configurations to be passed by its caller.
```

A measured nuance: an **empty** `provider` block only triggers
`Warning: Redundant empty provider block`. It is the block **carrying arguments**
that makes the module incompatible with `count`, `for_each` and `depends_on`.

## Passing a configuration to a module

Implicit inheritance only covers the **default** configuration: "Aliased providers
are never inherited automatically and must be passed explicitly using the
`providers` argument." Two declarations are therefore needed, one on each side.

On the module side, the expectation is declared in `required_providers`:

```hcl
terraform {
  required_providers {
    local = {
      source                = "hashicorp/local"
      version               = ">= 2.5"
      configuration_aliases = [local.plaques]
    }
  }
}

resource "local_file" "plaque" {
  provider = local.plaques

  filename = "${path.root}/${var.repertoire}/${var.nom}.txt"
  content  = "plaque ${var.nom}\n"
}
```

On the caller side, the configuration is **passed**:

```hcl
provider "local" {
  alias = "atelier"
}

module "plaque" {
  source = "../bibliotheque/plaque"

  providers = {
    local.plaques = local.atelier
  }

  nom        = "nord"
  repertoire = "sorties"
}
```

Forget the `providers` argument, and the `init` stops naming what is missing:

```text
Error: Missing required provider configuration

The child module requires an additional configuration for provider
hashicorp/local, with the local name "local.secondaire".
```

## Dependency inversion

This is the heart of the official composition page: a module **receives** what it
depends on, it does not **build** it. A module deciding alone about its output
directory, its network or its security group imposes its choices on every caller.

```hcl
# before: the module decides
locals {
  repertoire = "plaques"
}

# after: the caller decides
variable "repertoire" {
  type        = string
  description = "Repertoire ou ecrire la plaque."
}
```

The benefit is concrete: the caller can pass a resource it **creates**, or a `data
source` that **reads** an existing one, without the module changing by a line.

## Proving all this without reading the code

The plan JSON exposes the configuration **as Terraform understood it**. Two keys
are enough.

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.configuration.provider_config'
```

```json
{
  "local": { "name": "local", "full_name": "registry.terraform.io/hashicorp/local" },
  "module.plaque:local": {
    "name": "local",
    "full_name": "registry.terraform.io/hashicorp/local",
    "module_address": "module.plaque"
  }
}
```

The **`module_address`** field only appears for a configuration declared **inside a
module**: it is the exact detector of the violation. Conversely, an **aliased**
configuration passed by the caller appears with its `alias`, at root level.

The rest is read in the same document: `module_calls.<name>.module.variables` gives
the module's real interface, `expressions` what the caller passes it, and
`resources[].mode` separates what it **manages** from what it **reads**.

## The other rules that matter

The module tree stays **flat**: "we strongly recommend keeping the module tree
flat, with only one level of child modules". Relations run through **expressions**
between calls, not through a deep hierarchy.

A module **documents** itself: the Standard Module Structure puts `README.md` in
the **minimum**, and that file is what the registry and documentation generators
consume.

Finally, a reusable module constrains only its version **floor**, the upper bound
belonging to the root module.

## Your turn

You know why a module does not configure its provider, how to pass it one, what
dependency inversion is, and where to read the proof. The challenge hands you a
legacy module to make composable, and a project that must draw two plates from a
single call.

```bash
dsoxlab run modules-module-best-practices
dsoxlab check modules-module-best-practices
dsoxlab hint modules-module-best-practices
```

It runs **offline**.

Target exam sub-objective: **5b** (provider configurations in modules).

Reference: [module best practices](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/bonnes-pratiques-modules/)
