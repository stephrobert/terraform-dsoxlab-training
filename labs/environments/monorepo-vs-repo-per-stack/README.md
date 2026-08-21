# Splitting stacks splits state

Monorepo or one repo per stack is an organisational debate. Its **technical
consequence** is not: splitting into stacks splits **state**, and one stack sees
nothing of the other until you explicitly **publish** what it must share.

## A local module does not accept `version`

This is not a convenience you opt into, it is a **refusal**. Measured:

```hcl
module "reseau" {
  source  = "./modules/reseau"
  version = "~> 1.0"
}
```

```text
Error: Invalid registry module source address

Failed to parse module registry address: can't use local directory
"./modules/reseau" as a module registry address.

Terraform assumed that you intended a module registry source address because
you also set the argument "version", which applies only to registry modules.
```

`init` exits with **1**. The documentation explains why: "Modules sourced from
local file paths do not support `version` because they're loaded from the same
source repository and always share the same version as their caller."

A corollary that is often missed: **only** the registry form
(`source = "<NAMESPACE>/<NAME>/<PROVIDER>"`) accepts a **constraint** such as
`~> 1.3`. With `git::...?ref=v1.3.0`, versioning is a **literal pin**, not a
constraint Terraform resolves.

## Only ROOT outputs cross the boundary

This is trap number one when breaking up a monorepo. An output declared in a
**nested** module is not visible from another configuration. Measured, on an
upstream stack that calls a module and re-exports only one value:

```text
Error: Unsupported attribute

data.terraform_remote_state.amont.outputs is object with 1 attribute "reexporte"
This object does not have an attribute named "identifiant_interne".
```

Whatever must cross is therefore **re-exported** at the root:

```hcl
output "network_cidr" {
  value = module.reseau.network_cidr
}
```

## Publishing an output publishes the whole state

The documentation's warning deserves quoting in full:

> any user or server which has enough access to read the root module output
> values will also always have access to the full state snapshot data by direct
> network requests.

In other words, granting access to a stack's **outputs** grants access to the
**full snapshot** of its state. A password therefore has no place in a root
output, **even** marked `sensitive`: that argument hides the display, not the
state.

Measured: `terraform output -json` does return a `sensitive` value **in clear**;
only the text output masks it.

The documentation recommends explicit publication to a dedicated store instead of
sharing state.

## Two useful arguments of `terraform_remote_state`

**`defaults`** fills in a **missing** output in a state that **exists**:

```hcl
data "terraform_remote_state" "amont" {
  backend = "local"

  config = {
    path = "../amont/terraform.tfstate"
  }

  defaults = {
    identifiant = "valeur-de-repli"
  }
}
```

Measured: the fallback is indeed used when the output is absent. If the upstream
state does **not exist at all**, however, `defaults` saves nothing:

```text
Error: Unable to find remote state

No stored state was found for the given workspace in the given backend.
```

**`workspace`** names the upstream workspace to read. Careful though: on a
`local` backend whose `path` points at a specific **file**, the measurement
returns the same `Unable to find remote state`. That argument makes sense on a
backend that addresses its workspaces natively.

## Your turn

```bash
dsoxlab run environments-monorepo-vs-repo-per-stack
dsoxlab check environments-monorepo-vs-repo-per-stack
dsoxlab hint environments-monorepo-vs-repo-per-stack
```

It runs **offline**, on the `local` and `random` providers.

Exam sub-objective covered: **3d**, with **3b** in support.

Reference: [monorepo vs repo per stack](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/monorepo-vs-repo-par-stack/)
