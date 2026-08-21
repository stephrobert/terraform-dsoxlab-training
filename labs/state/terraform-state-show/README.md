# `terraform state show`: a sheet for your eyes, not for a script

`terraform state show <address>` prints the sheet of **one** instance recorded in
the state. It is the comfortable read after a `terraform state list`. But the
official documentation is blunt: that output is meant for **human consumption**,
not programmatic. This tutorial shows what it displays, above all what it
**hides**, and what to use instead as soon as a script depends on it.

## One instance at a time, and the address must be exact

The command takes a single address, and that address must designate **one
specific instance**. This is the first wall after a `state list`:

```bash
terraform state show random_pet.noeud
```

```text
No instance found for the given address!

This command requires that the address references one specific instance.
To view the available instances, use "terraform state list". Please modify
the address to reference a specific instance.
```

The exit code is **1**. On a resource created with `count` or `for_each` you
therefore need the index or the key:

```bash
terraform state show 'random_pet.noeud[1]'
terraform state show 'random_pet.zone["eu-west"]'
terraform state show data.local_file.lecture
```

The single quotes are not decorative: under `zsh`, brackets are a filename
pattern and the command fails before it even reaches Terraform.

## What the sheet displays

For an unremarkable resource, the sheet reads directly:

```bash
terraform state show random_pet.env
```

```text
# random_pet.env:
resource "random_pet" "env" {
    id        = "happy-lizard"
    length    = 2
    separator = "-"
}
```

Three attributes, and that is all. Remember that number: the state holds
**five**.

## First blind spot: null attributes disappear

An attribute set to `null` is **omitted** from the sheet. It does exist in the
state, and the JSON output shows it:

```bash
terraform show -json | jq '.values.root_module.resources[]
  | select(.address == "random_pet.env") | .values'
```

```json
{
  "id": "happy-lizard",
  "keepers": null,
  "length": 2,
  "prefix": null,
  "separator": "-"
}
```

`keepers` and `prefix` appeared nowhere in the sheet. Direct consequence: a
`grep keepers` on the output of `state show` returns nothing, and you wrongly
conclude the provider does not support the attribute. The right question is not
"does the provider know it", but "is it `null`".

## Second blind spot: sensitive values are redacted

A sensitive attribute is replaced by a marker:

```bash
terraform state show random_password.api
```

```text
# random_password.api:
resource "random_password" "api" {
    bcrypt_hash = (sensitive value)
    id          = "none"
    length      = 24
    ...
    result      = (sensitive value)
}
```

That is useful protection: the sheet can be shown to someone without leaking the
secret. But it makes the value unreachable through this path. To learn **which**
attributes Terraform treats as sensitive, the JSON carries a dedicated object:

```bash
terraform show -json | jq '.values.root_module.resources[]
  | select(.address == "random_password.api") | .sensitive_values'
```

```json
{
  "bcrypt_hash": true,
  "result": true
}
```

## Switching to JSON, and its downside

As soon as a value must serve anywhere other than under your eyes, the docs name
the correct path: `terraform show -json`, then decode the documented structure.
Careful, `terraform state show` has **no** `-json` option:

```bash
terraform state show -json random_pet.env
```

```text
Failed to parse command-line flags
flag provided but not defined: -json
```

It is `terraform show -json`, without `state`, that produces the full document.

The downside matters: **JSON exposes sensitive values in plain text**. The
official page says so plainly, "any sensitive values in Terraform state will be
displayed in plain text". Where `state show` protects, `show -json` reveals. A
`terraform show -json` redirected into a pipeline artefact therefore drops your
secrets in it.

## Third trap: `state show` refreshes nothing

The command reads **the recorded state**. It does not query the infrastructure.
Modify an object outside Terraform, then run the sheet again: it is
**unchanged**, checksums included. It is the following `terraform plan`, which
does refresh, that reveals the drift and exits with code **2** under
`-detailed-exitcode`.

`state show` therefore shows the gap between the state and your code, **never**
between the state and reality. Telling them apart keeps you from concluding "all
good" on a resource changed behind Terraform's back.

## Your turn

You know an instance address is required, index included; that the sheet omits
null attributes and redacts sensitive ones; that `terraform show -json` is the
only reliable path for a script, at the cost of exposing secrets; and that
`state show` refreshes nothing. The challenge has you fill five outputs that can
only come from the state, two of them values the human sheet refuses to show.

```bash
dsoxlab run state-terraform-state-show
dsoxlab check state-terraform-state-show
dsoxlab hint state-terraform-state-show
```

Target exam objective: **1e** (inspect and manipulate state), Associate level.

Reference: [terraform state show](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-show/)
