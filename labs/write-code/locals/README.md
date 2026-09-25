# Local values, and when they get computed

A **`locals` block** names computed values, so the same expression is not
repeated in ten places. Simple on the face of it, but three things surprise
people: several `locals` blocks **merge**, a ternary **converts its types
without warning**, and a local derived from a resource is **not known at plan
time**. This tutorial shows them on a **throwaway** shop example, then the
challenge has you chain all three traps on another case.

Most of the checks happen in `terraform console`, which evaluates an expression
without applying anything.

## A local is a name for an expression

The syntax boils down to `name = expression`. A local **accepts neither `type`,
nor `description`, nor `sensitive`, nor `validation`**: that is the whole
difference with a variable, which can be typed and documented. A local is an
internal, computed value that nothing overrides from outside.

```hcl
variable "enseigne" {
  type    = string
  default = "Ma_Boutique"
}

locals {
  ref = replace(lower(var.enseigne), "_", "-")
}
```

A local can reference **four** things: a **variable**, a **resource
attribute**, a **function's output**, and **another local**. The first two
examples above show it: `local.ref` normalises `var.enseigne` with two
functions.

## Several locals blocks merge

You can write as many `locals {}` blocks as you like, in one file or several.
Terraform **merges** them: a local in one block can reference another declared
elsewhere, as long as no cycle appears.

```hcl
locals {
  etiquette = "${local.ref}-${var.palier}"
}
```

```bash
terraform console
```

```hcl
> local.etiquette
"ma-boutique-gold"
```

`local.etiquette` (in a second block) consumes `local.ref` (in the first), and
the result is properly normalised.

## The ternary trap: types convert in silence

Here is the most frequent mistake. People often believe a ternary whose two
branches have different types **fails**. It does not: Terraform **converts to a
common type without complaining**.

```hcl
locals {
  remise = var.palier == "gold" ? 20 : 5
}
```

```hcl
> type(local.remise)
number
```

Good. But slip a quote around a number, and everything shifts:

```hcl
> type(true ? 20 : "5")
string

> type(true ? 20 : 5)
number
```

`20 : "5"` raises **no error**, it returns a **string**. A local meant to carry
a number ends up typed as a string, and the bug shows up much further along,
where that number gets used. The documentation does recommend being explicit
when in doubt, with a conversion function:

```hcl
> true ? tostring(20) : "cinq"
"20"
```

The simple rule: do not put quotes around a number, and if the two branches
really differ, convert them explicitly.

## A local derived from a resource is unknown at plan time

A local is computed during the **plan**, unless it references a **resource
attribute** that does not exist yet. In that case its value is
`(known after apply)`, exactly like the attribute it depends on.

```hcl
resource "random_id" "tirage" {
  byte_length = 4
}

locals {
  empreinte = upper(random_id.tirage.hex)
}
```

On a cold plan, an output exposing `local.empreinte` shows up as unknown:
`random_id.tirage.hex` is only produced at apply time, and the local inherits
that unknown. The JSON plan shows it under `output_changes[].after_unknown`.
That is also what creates an **implicit dependency** in the graph: the local
depends on the resource.

## Sensitivity propagates through a local

The last trap, and it blocks the apply. Terraform treats as **sensitive any
expression using a sensitive value**. A local assembling a string from a
`sensitive = true` variable therefore becomes sensitive itself:

```hcl
variable "mot_de_passe" {
  type      = string
  sensitive = true
}

locals {
  dsn = "postgres://app:${var.mot_de_passe}@localhost/base"
}
```

An `output` exposing `local.dsn` **without** `sensitive = true` makes Terraform
fail:

```text
Error: Output refers to sensitive values
```

The fix is to annotate the output with `sensitive = true`. Sensitivity is not a
property you choose, it propagates on its own.

## Over to you

You know a local is not a variable, that blocks merge, that a ternary converts
its types, that a local can be unknown at plan time, and that sensitivity
propagates. The challenge has you build a chain of locals crossing those traps,
and the tests prove them in the JSON.

```bash
dsoxlab run write-code-locals
dsoxlab check write-code-locals
dsoxlab hint write-code-locals
```

Exam objective targeted: **2c** (Terraform Authoring and Operations
Professional), spilling into 2f for sensitivity.

Reference: [local values in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/locals-terraform/)
