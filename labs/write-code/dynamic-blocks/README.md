# Generate blocks, and know when not to

A **`dynamic`** block builds nested blocks from a collection, wherever the
provider's schema exposes a repeatable block. It is the tool when the **number**
of blocks comes from a variable rather than from typing. But it has a wall: it
cannot generate a **meta-argument** block such as `lifecycle`. This tutorial
teaches both faces on a **throwaway** example, a bundle of files, then the
challenge has you apply it to a cloud-init document.

The example rests on `archive_file`, whose `source` block is repeatable and runs
locally, with no cloud:

```hcl
terraform {
  required_providers {
    archive = { source = "hashicorp/archive", version = "~> 2.4" }
  }
}
```

## A dynamic block repeats a provider block

The principle: replace several identical blocks with a single `dynamic` block
generating them. Its **`for_each`** supplies the collection, its **`content`**
block describes the block to produce, and an iteration variable, named after the
block by default, gives access to the current element.

```hcl
locals {
  entrees = {
    "config.yaml" = "cle: valeur\n"
    "notes.txt"   = "rien a signaler\n"
  }
}

data "archive_file" "bundle" {
  type        = "zip"
  output_path = "${path.module}/bundle.zip"

  dynamic "source" {
    for_each = local.entrees
    content {
      filename = source.key
      content  = source.value
    }
  }
}
```

The `dynamic "source"` block generates as many `source` blocks as the map has
entries. The iteration variable carries the block's name, `source`, and gives
`source.key` (the key) and `source.value` (the value). After an `apply`:

```bash
terraform output nb_fichiers   # length(...source)
```

```text
2
```

Two entries in the map, two `source` blocks generated.

## Filtering happens in for_each, never in content

This is the most frequent mistake. To include only some of the elements, filter
**the collection** with a `for` expression, inside `for_each`:

```hcl
dynamic "source" {
  for_each = { for k, v in local.entrees : k => v if length(v) > 0 }
  content {
    filename = source.key
    content  = source.value
  }
}
```

Putting an `if` inside the `content` is pointless: the block is already decided
at that stage. The number of blocks is settled upstream, on the collection.

## Renaming the iteration variable with iterator

By default, the variable carries the block's name. When a nested block has the
**same name as its parent**, or for readability, the **`iterator`** argument
renames it:

```hcl
dynamic "source" {
  for_each = local.entrees
  iterator = fichier
  content {
    filename = fichier.key
    content  = fichier.value
  }
}
```

`terraform validate` accepts it, and the `content` now reaches `fichier.key` and
`fichier.value`. That is the only way to tell two levels apart when one `dynamic`
contains another of the same name.

## The .key trap on a set

`for_each` accepts a map or a **set**. On a set there is a documented subtlety:
**`key` is identical to `value`**, and should not be used.

```hcl
locals {
  lignes = toset(["alpha", "bravo"])
}

dynamic "source" {
  for_each = local.lignes
  content {
    filename = "${source.key}.txt"
    content  = source.value
  }
}
```

```bash
terraform output noms
```

```text
["alpha.txt", "bravo.txt"]
```

Here `source.key` is `"alpha"` then `"bravo"`, exactly like `source.value`: on a
set, the two are conflated. Use `source.value`, and keep `source.key` for maps,
where the key has a meaning of its own.

## The wall: dynamic does not generate a meta-argument block

A `dynamic` repeats a **provider** block (`source`, `ingress`, `setting`). It
**cannot** generate a meta-argument block such as `lifecycle` or `provisioner`,
because Terraform must process those blocks **before** evaluating any
expression. Those blocks are always written literally.

If you try a `dynamic` on a block the context does not expect, the message names
the **label** aimed at, never the word `dynamic`:

```hcl
dynamic "reglage" {
  for_each = [1]
  content { option = reglage.value }
}
```

```text
Error: Unsupported block type
Blocks of type "reglage" are not expected here.
```

Remember that message: it is the one you will see if you put a `dynamic` on a
non-existent block, or on a meta-argument. The challenge has you hit it with a
`dynamic "lifecycle"`, precisely to make you write the `lifecycle` block by hand.

## To be used sparingly

A `dynamic` makes a configuration harder to read than a series of literal
blocks. The official documentation advises against it for simple cases: keep it
for blocks whose **number** really depends on a variable. A block that never
varies, such as a common header, stays literal.

## Over to you

You can now generate blocks, filter in the `for_each`, rename with `iterator`,
and recognise the meta-argument wall. The challenge applies all of it to a
cloud-init document, with a booby-trapped `dynamic "lifecycle"` to dismantle:

```bash
dsoxlab run write-code-dynamic-blocks
dsoxlab check write-code-dynamic-blocks
dsoxlab hint write-code-dynamic-blocks
```

Exam objective targeted: **2d** (Terraform Authoring and Operations
Professional).

Reference: [dynamic blocks in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/blocs-dynamiques/)
