# Repair first, then let the data drive

The Professional's second objective, and the broadest: validate, query, compute,
use meta-arguments, type variables, protect secrets. This capstone fits them into
a single configuration, in two stages.

**First repair.** The configuration shipped does not even pass `terraform init`.
**Then build.** One entry in a variable must produce a complete set of resources,
without a single duplicated line.

The lab runs **offline**, on `local`, `null`, `random` and `archive`.

## The three errors do not fall at the same time

That is the first lesson, and it surprises people.

```console
$ terraform init
│ Error: Invalid combination of "count" and "for_each"
$ echo $?
1
```

**`init` parses the configuration.** While an error of that kind remains, no
provider is installed. And `validate`, run in that state, answers:

```console
$ terraform validate
│ Error: Missing required provider
```

That message has nothing to do with your errors, and sends you looking in the
wrong place. So the method is: **init, fix what it refuses, init again, then
validate**.

The two other errors then appear together, with their line numbers:

```console
$ terraform validate
│ Error: Incorrect attribute value type    on main.tf line 41
│ Error: Reference to undeclared input variable    on main.tf line 64
```

## `count` or `for_each`, and why the choice is not neutral

Terraform refuses both on the same resource. The choice comes down to one
question: **how are instances addressed in state?**

| Meta-argument | Address | Removing the middle entry |
| --- | --- | --- |
| `count` | by position, `[0]`, `[1]` | shifts the following ones, which are **destroyed and recreated** |
| `for_each` | by key, `["PROD_EU"]` | touches only that one |

On three local files the difference costs nothing. On three databases it costs
the data.

## A name is computed, not copied

```hcl
locals {
  noms = {
    for cle, _ in var.environnements :
    cle => substr("${var.prefixe}-${replace(lower(cle), "_", "-")}", 0, var.longueur_nom)
  }
}
```

`PreProd_EU` becomes `lab-preprod-eu`. Three chained functions, and the rule
holds for a key you have never seen: that is exactly what the last test checks,
by adding an environment.

## Filtering happens in the `for_each`, never in the `content`

```hcl
dynamic "source" {
  for_each = each.value.options
  content {
    filename = "${source.value}.txt"
    content  = "option ${source.value} activee\n"
  }
}
```

An environment with no option produces **no** block, without a single `if`
clause. That is the most frequent mistake with `dynamic`: putting an `if` in the
`content` does not reduce the number of blocks, the block is already decided at
that point.

Measured on the target configuration, the `source` block count per environment:
**2**, **3** and **1**, that is the fixed block plus one per declared option.

## Sensitivity is not optional

```hcl
output "secrets" {
  value     = { for cle, _ in var.environnements : local.noms[cle] => random_password.secret[cle].result }
  sensitive = true
}
```

Without `sensitive = true`, Terraform **refuses to plan**: the value derives from
a `random_password`, so it treats it as sensitive, and the message mentions
"sensitive values". That is not a courtesy, it is a refusal.

## What really tells `for_each` from three copied blocks

Nothing, as long as you look at the result for these three environments. Every
test would pass on a hand-written configuration.

Which is why the last one **changes the variable**: it copies the directory, adds
a fourth environment, applies, and requires everything to follow — four
manifests, a normalised name for a key never seen before, and an archive with
four blocks. Hand-written blocks cannot follow.

## Over to you

```bash
dsoxlab run certifications-professional-capstone2-dynamic-config
dsoxlab check certifications-professional-capstone2-dynamic-config
dsoxlab hint certifications-professional-capstone2-dynamic-config
```

Nine tests. They read `validate -json`, `show -json` and `output -json`, never
your files.

Exam objective targeted: **2**, across its six sub-objectives.

Reference: [the Terraform Authoring and Operations Professional syllabus](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
