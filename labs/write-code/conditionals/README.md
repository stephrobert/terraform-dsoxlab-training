# Place each guard rail at the right level

Terraform offers **four** mechanisms for refusing an absurd value, and the trap
is not writing a condition: it is placing it in the right spot. A `validation`
block, a `precondition`, a `postcondition` and a `check` block are not evaluated
at the same moment and do not block the same thing.

This tutorial builds them one by one on a **throwaway** example: a purchase order
computing a total and refusing it when absurd. The challenge then has you
transpose those four tools to another case. The lab runs on the `local` provider
alone.

## Setting up the example

In a separate directory, a `main.tf` declaring a region, a quantity and a
receipt:

```hcl
variable "region" {
  type    = string
  default = "eu-ouest"
}

variable "quantite" {
  type    = number
  default = 10
}

locals {
  total = var.quantite * 10
}

resource "local_file" "recu" {
  filename = "${path.module}/recu.json"
  content  = jsonencode({ region = var.region, quantite = var.quantite, total = local.total })
}
```

Run `terraform init`. You will add each guard rail as the sections go.

## validation: filtering an input variable

The simplest mechanism lives on the variable itself, and refuses the value
**before** the plan is even generated. Add a `validation` block to `region`:

```hcl
variable "region" {
  type    = string
  default = "eu-ouest"

  validation {
    condition     = contains(["eu-ouest", "eu-nord", "us-est"], var.region)
    error_message = "region inconnue."
  }
}
```

```bash
terraform plan -var 'region=lune'
```

```text
Error: Invalid value for variable

  on main.tf line 1:
```

The plan stops dead. Key point: a `validation` **only sees its own variable**. It
can say nothing about a `local` nor about a resource's result.

## A validation that looks at another variable

Since Terraform 1.9, a `validation` can reference **another variable**. Add an
express option, valid in one region only:

```hcl
variable "express" {
  type    = bool
  default = false

  validation {
    condition     = !var.express || var.region == "eu-ouest"
    error_message = "l'option express n'existe qu'en eu-ouest."
  }
}
```

The condition reads "no express, **or** region eu-ouest". Try both cases:

```bash
terraform plan -var 'express=true' -var 'region=us-est'
```

```text
Error: Invalid value for variable

  on main.tf line 16:
```

```bash
terraform plan -var 'express=true' -var 'region=eu-ouest'
```

That second plan passes. The rule only fires in the targeted combination.

## precondition: checking before the action

Some checks bear on a computed value, out of reach of a `validation`. The
`precondition` lives in the resource's `lifecycle` block and is evaluated
**before** writing it. Require a quantity of at least 1:

```hcl
resource "local_file" "recu" {
  filename = "${path.module}/recu.json"
  content  = jsonencode({ region = var.region, quantite = var.quantite, total = local.total })

  lifecycle {
    precondition {
      condition     = var.quantite >= 1
      error_message = "quantite doit valoir au moins 1."
    }
  }
}
```

```bash
terraform plan -var 'quantite=0'
```

```text
Error: Resource precondition failed

  on main.tf line 36, in resource "local_file" "recu":
```

The precondition blocks before the file is written.

## postcondition: checking the actual result

A `postcondition` is evaluated **after** the action and sees the produced object
through `self`. Add it under the precondition to guarantee the receipt does carry
a total:

```hcl
    postcondition {
      condition     = can(jsondecode(self.content).total)
      error_message = "le recu ne porte pas de total."
    }
```

It is the only mechanism that has `self`. A `validation` or a `precondition`
cannot read back a result that does not exist yet when they are evaluated.

## check: warning without blocking

The first four mechanisms **stop** Terraform. Sometimes you only want a signal.
The `check` block is written **at root level**, never inside a resource:

```hcl
check "quota_mensuel" {
  assert {
    condition     = local.total <= 1000
    error_message = "quota mensuel depasse."
  }
}
```

Push the quantity past the quota and apply:

```bash
terraform apply -var 'quantite=120'
```

```text
Warning: Check block assertion failed

  on main.tf line 48, in check "quota_mensuel":

Apply complete! Resources: 1 added, 0 changed, 1 destroyed.
```

That is a **Warning**, not an **Error**, and the apply completes. A `check`
observes and reports, it does not keep the gate.

## Reading where each guard was placed

The JSON plan exposes a `checks` array whose `kind` field proves each check's
**level**:

```bash
terraform show -json | jq -c '.checks[] | {kind: .address.kind, addr: .address.to_display, status}'
```

```text
{"kind":"check","addr":"check.quota_mensuel","status":"fail"}
{"kind":"resource","addr":"local_file.recu","status":"pass"}
{"kind":"var","addr":"var.express","status":"pass"}
{"kind":"var","addr":"var.region","status":"pass"}
```

`kind: var` for validations, `kind: resource` for the precondition and the
postcondition, `kind: check` for the block. And `quota_mensuel` is `fail`
although the apply succeeded: proof, in the data, that a `check` does not block.

## Over to you

You can now tell the four guard rails apart by their level and their effect. The
challenge applies all of it to another setting, and the tests check the `kind` of
every control you place:

```bash
dsoxlab run write-code-conditionals
dsoxlab check write-code-conditionals
dsoxlab hint write-code-conditionals
```

| Mechanism | Bears on | Evaluated | On failure | `kind` |
|---|---|---|---|---|
| `validation` | an input variable | before the plan | stops | `var` |
| `precondition` | any expression, including a `local` | before the action | stops | `resource` |
| `postcondition` | the actual result, through `self` | after the action | stops | `resource` |
| `check` block | any expression | at apply time | **warns only** | `check` |

The choice does not depend on the condition to write, but on two questions:
**what** does the check bear on, and **must it block**?

Exam objective targeted: **2a** (Terraform Authoring and Operations
Professional).

Reference: [validating a Terraform configuration's inputs](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/conditions-terraform/)
