# Transform a collection with for expressions

A **`for` expression** turns one collection into another: filtering, renaming,
grouping, crossing two levels. It is the tool that replaces copy-paste when the
same data has to come out in several shapes. This tutorial teaches it on a
**throwaway** example, a handful of teams, then lets you apply it to another
catalogue in the challenge.

Everything is tested in `terraform console`, without writing a single resource.
That is the reflex to acquire: try the expression out, then write it. First set
up the working data in a separate directory:

```hcl
locals {
  equipes = {
    alpha = { pole = "produit", effectif = 4, competences = ["go", "k8s"] }
    bravo = { pole = "produit", effectif = 6, competences = ["go"] }
    delta = { pole = "data", effectif = 3, competences = [] }
  }
}
```

```bash
terraform console
```

## Brackets or braces: tuple or object

This is the subject's most important distinction, and it decides everything else.
**Brackets `[ ]` produce a tuple, braces `{ }` produce an object.** Terraform
never confuses the two, and the `type()` function shows it:

```hcl
> type([for k, v in local.equipes : k])
tuple([string, string, string])

> type({for k, v in local.equipes : k => v.effectif})
object({alpha: number, bravo: number, delta: number})
```

Remember it: the shape of the delimiters dictates the shape of the result. A
tuple is an ordered sequence; an object maps keys to values. The object syntax
carries an arrow `k => v` that the tuple does not have.

## Filtering a list

The most common form extracts a sublist. Between brackets, you iterate the map
and keep only the wanted keys:

```hcl
> [for k, v in local.equipes : k]
[
  "alpha",
  "bravo",
  "delta",
]
```

The order is no accident: a `for` expression over a map **iterates the keys
sorted lexically**. No need to reorder by hand. An `if` clause, placed after the
expression, filters the iteration:

```hcl
> [for k, v in local.equipes : k if v.pole == "produit"]
[
  "alpha",
  "bravo",
]
```

The condition sees both iteration variables, the key as well as the value. So
you can just as well filter on the key:

```hcl
> [for k, v in local.equipes : k if k != "delta"]
[
  "alpha",
  "bravo",
]
```

## Building a map

With braces and an arrow, the same iteration produces an object. Here the team's
name becomes the key, the headcount the value:

```hcl
> {for k, v in local.equipes : k => v.effectif}
{
  "alpha" = 4
  "bravo" = 6
  "delta" = 3
}
```

## Grouping with the ellipsis

What happens when two entries produce the **same key**? By default Terraform
refuses. `alpha` and `bravo` both belong to the `produit` division:

```hcl
> {for k, v in local.equipes : v.pole => k}

Error: Duplicate object key

Two different items produced the key "produit" in this 'for' expression. If
duplicates are expected, use the ellipsis (...) after the value expression to
enable grouping by key.
```

The message itself gives the remedy: **the ellipsis `...`** after the value
expression enables grouping mode. Each key then carries the **list** of values,
instead of overwriting them:

```hcl
> {for k, v in local.equipes : v.pole => k...}
{
  "data" = [
    "delta",
  ]
  "produit" = [
    "alpha",
    "bravo",
  ]
}
```

The ellipsis only exists with braces. Applying it to a tuple
(`[for ... : k...]`) fails with "Grouping ellipsis (...) cannot be used when
building a tuple": grouping only makes sense by key.

## The splat, and its trap on a map

Terraform offers a short form, the **splat `[*]`**, replacing a simple `for` over
a list: `var.liste[*].id` is equivalent to `[for o in var.liste : o.id]`. Handy,
as long as you apply it to a list.

On a **map**, the splat becomes a trap, because it **raises no error**. It wraps
the whole map in a single-element tuple:

```hcl
> length(local.equipes[*])
1
```

`1`, not `3`. The configuration keeps validating, and breaks further along, where
three entries were expected. A resource driven by `for_each` being itself a map,
the splat is just as unsuitable for it. **On a map, always write an explicit
`for` expression**, never a splat.

## Crossing two levels: flatten

As soon as two dimensions have to be combined, each team and each of its skills,
you nest two `for` expressions. The result is a list of lists, which `flatten`
flattens:

```hcl
> flatten([for k, v in local.equipes : [for comp in v.competences : "${k}:${comp}"]])
[
  "alpha:go",
  "alpha:k8s",
  "bravo:go",
]
```

Note `delta`: its skill list is empty, the inner loop produces nothing, and
`flatten` absorbs it naturally. No `delta:` entry in the result, without a single
`if` clause to exclude it.

## Validating a whole collection

Combined with `alltrue`, a `for` expression checks a property on **every**
element of a collection, which a simple test cannot do:

```hcl
> alltrue([for k, v in local.equipes : v.effectif > 0])
true
```

That is the pattern for validating a complex-typed variable: the function returns
`true` only if the condition holds for every entry.

## What a for expression cannot do

A `for` expression only generates **collection values**. It **cannot** produce
nested configuration blocks: to repeat an `ingress` or `setting` block inside a
resource, you need a `dynamic` block, not a `for`. Confusing the two is a
frequent dead end.

## Over to you

You can now filter, build a map, group, flatten, and avoid the splat on a map.
The challenge applies all of it to another catalogue, and checks every shape in
`terraform output -json`:

```bash
dsoxlab run write-code-for-loops
dsoxlab check write-code-for-loops
dsoxlab hint write-code-for-loops
```

Keep the console reflex: a `for` expression is validated in three seconds before
it goes into a `local`.

Exam objective targeted: **2c** (Terraform Authoring and Operations
Professional).

Reference: [for expressions in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/boucles-for-terraform/)
