# A registry module is downloaded, versioned, and never locked

A local module is read in place. A **registry** module is **downloaded** into
`.terraform/modules/`, and it carries a **version**. That version is the one real
problem of the topic: `.terraform.lock.hcl`, which locks your providers, **locks
no module at all**.

## The three-part address

A registry source is written `namespace/name/provider`, with no `./` or `../`
prefix:

```hcl
module "etiquette" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  namespace = "demo"
  name      = "ouest"
}
```

That format is not arbitrary, it is **derived** from the published repository. The
publishing rule imposes a three-part repository name,
`terraform-<PROVIDER>-<NAME>`: the repository `cloudposse/terraform-null-label`
therefore yields the address `cloudposse/label/null`. `<PROVIDER>` need not be a
cloud, here it is `null`.

## What `init` downloads

```text
Initializing modules...
Downloading registry.terraform.io/cloudposse/label/null 0.25.0 for etiquette...
- etiquette in .terraform/modules/etiquette
```

The module registry file records **three** pieces of information where a local
module had only two:

```json
{
  "Key": "etiquette",
  "Source": "registry.terraform.io/cloudposse/label/null",
  "Version": "0.25.0",
  "Dir": ".terraform/modules/etiquette"
}
```

The **`Version`** key exists **only** for a registry module. And `Dir` now points
**inside** `.terraform/`, the copy being genuine: the downloaded folder holds the
repository's files, `main.tf`, `variables.tf`, `outputs.tf`, but also its
`README.md`, its `examples/` and its `.git`.

## `version` is optional, and that is a trap

Remove the `version` argument: the `init` **still succeeds**.

```text
Downloading registry.terraform.io/cloudposse/label/null 0.25.0 for etiquette...
```

Terraform picked the **newest** available. Nothing forbids it, and that is exactly
what makes the omission dangerous: the same code, initialised tomorrow on another
machine, will take **another** version.

## The lock file does not cover modules

This is the least-known fact of the topic, and the documentation does not hide it:
"At present, the dependency lock file tracks only **provider** dependencies.
Terraform does not remember version selections for remote modules."

Two observations prove it. In a project that declares a provider, the lock speaks
**only** of it:

```bash
grep -c cloudposse .terraform.lock.hcl
```

```text
0
```

And in a project whose **only** dependency is a registry module, there is **no
lock file at all**. Nothing is pinned on the module side, then, beyond what you
write yourself in `version`.

## Why your `~> 0.24` stays stuck

Here is the behaviour nobody guesses and everybody eventually meets. Under a
flexible constraint, the version retained at the first `init` **stays installed**
on later ones:

```text
$ terraform init          # first init, constraint ~> 0.24
Downloading registry.terraform.io/cloudposse/label/null 0.24.1 for etiquette...

$ terraform init          # second init, nothing moves
Initializing modules...
```

`modules.json` still carries `0.24.1`, while `0.25.0` exists and satisfies the
constraint. The documentation explains it: "Terraform uses the newest
**installed** version of the module that meets the constraint." A single option
unblocks the situation:

```text
$ terraform init -upgrade
Upgrading modules...
Downloading registry.terraform.io/cloudposse/label/null 0.25.0 for etiquette...
```

Note the nuance: on a **fresh** machine or in **CI**, no copy is installed, so the
newest is retained **without** `-upgrade`. The same code does not install the same
version on your desk and in the pipeline.

## An exact constraint also pins downwards

Changing the constraint to an **earlier** version needs no `-upgrade`: the
installed copy no longer satisfies the constraint, so Terraform downloads.

```text
$ terraform init          # the constraint moves from "0.25.0" to "0.24.1"
Downloading registry.terraform.io/cloudposse/label/null 0.24.1 for etiquette...
```

Remember the underlying rule: `init` **keeps** the installed copy as long as it
satisfies the constraint, and **downloads** as soon as it does not. `-upgrade`
forces the re-evaluation in every case.

## The `//` sub-directory, and the order that matters

`//` is not a registry notion but a **package** one: it designates a
sub-directory inside whatever Terraform downloaded, Git repository or archive
included. On a Git source it coexists with the `?ref=` argument, and the order of
the two is **not free**: "the sub-directory portion must be **before** those
arguments".

```hcl
# correct
source = "git::https://example.com/reseau.git//modules/vpc?ref=v1.2.0"
```

The reverse order produces an error that names the real culprit, the revision:

```text
Error: Failed to download module

error downloading '...?ref=0.25.0%2F%2Fexports': invalid ref: "0.25.0//exports"
```

Terraform took `0.25.0//exports` for a revision name, which it is not.

## What `version` does not do

On a **Git** source, `version` does not exist: `?ref=` is what pins, and it
accepts a tag, a branch or a commit. On a **local** source, `version` is outright
refused, the `init` stopping on `Invalid registry module source address`. The
official rule is plain: "You can only use the `version` argument when the `source`
argument points to a module listed in a registry".

## Proving the installed version

Two artefacts, two different pieces of information, and you need **both**:

| Artefact | What it gives |
| --- | --- |
| `.terraform/modules/modules.json` | the **resolved** version, actually installed |
| `terraform show -json <plan>` | the **constraint** written, under `module_calls.<name>.version_constraint` |

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.configuration.root_module.module_calls'
```

A flexible constraint with an old installed version is exactly the case the human
output does not show and these two files expose.

## Your turn

You can read the three-part address, know what `init` downloads, why the lock
ignores modules, how an installed copy survives a flexible constraint, and where
to put a `//` facing a `?ref=`. The challenge hands you three projects: one to
pin, one to leave flexible, one to address by sub-directory.

```bash
dsoxlab run modules-module-registry
dsoxlab check modules-module-registry
dsoxlab hint modules-module-registry
```

This lab requires **network access** to `registry.terraform.io` and to
`github.com`.

Target exam sub-objective: **4b** (use a module), Associate level.

Reference: [using a registry module](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/module-registry/)
