# Refactor a copy-pasted project without destroying anything

The most common anti-pattern is not exotic: it is the **copy-pasted resource**. Two
nearly identical blocks, then three, then ten, and nothing is reusable any more.
Fixing it is easy; fixing it **without destroying** what is running is much less
so, and that is where the topic gets serious.

## What Terraform sees when you refactor

Terraform does not track resources, it tracks **addresses**. Extracting
`local_file.plaque_nord` into `module.plaque["nord"].local_file.plaque` changes that
address, and by default it draws the only possible conclusion: the old one is gone,
the new one must be created.

```text
Plan: 2 to add, 0 to change, 2 to destroy.
```

On files, that is harmless. On a database, a disk or a DNS record, it is an
**incident**. The `moved` block exists for this: it declares that one address
**replaces** another.

```hcl
moved {
  from = local_file.plaque_nord
  to   = module.plaque["nord"].local_file.plaque
}
```

The plan then changes nature entirely:

```text
  # local_file.plaque_nord has moved to module.plaque["nord"].local_file.plaque
  # random_pet.jeton_nord has moved to module.plaque["nord"].random_pet.jeton

Plan: 0 to add, 0 to change, 0 to destroy.
```

## How to know whether you really destroyed something

An honest check cannot rely on just any identifier. A `local_file` one is a **hash
of its content**: destroy the file, recreate it identically, and the `id` is the
**same**. A **non-deterministic** identifier, however, does not lie.

```bash
terraform output jetons
```

```text
{
  "nord" = "becoming-gull"
  "sud"  = "stirring-porpoise"
}
```

Those tokens come from a `random_pet`. If they change, the resource was
**recreated**, whatever the plan summary claimed. The principle carries well beyond
this lab: **pick as your witness a value the tool cannot recompute**.

## What `moved` does not do

The symmetric mistake is treating it as a magic wand. A `moved` handles
**addresses**, nothing else:

| Defect | Does `moved` fix it? |
| --- | --- |
| resource moved, renamed, pushed into a module | **yes** |
| managed resource to be turned into a data source | **no**, the documentation forbids it explicitly |
| untyped variable, hardcoded value | **no**, nothing to do with addressing |
| `provider` block declared inside a module | **no**, and its removal has its own trap |

That last point deserves one more line. Removing a provider configuration before
the resources it manages produces a **planning error**: "you must ensure that all
resources that belong to a particular provider configuration are destroyed before
you can remove that provider configuration's block".

## Abstraction, not merely factoring

Extracting copy-pasted code into a module is not enough to make it a **good**
module. The documentation offers a simple test: "If you have trouble finding a name
for your module that isn't the same as the main resource type inside it, that may
be a sign that your module is not creating any new abstraction." A module named
`local_file` abstracts nothing, it **wraps**.

This lab's module is called `plaque`, and rightly so: it produces a domain object,
made of a file **and** a token. The caller handles plates, not files.

## Type the input, document the contract

A variable without a `type` accepts **`any`**: a calling mistake then shows up only
when the value is **used**, sometimes never. An explicit object closes that door,
and turns the variable into a **contract**.

```hcl
variable "plaque" {
  type = object({
    etiquette = string
    intitule  = string
  })
  description = "Etiquette de la plaque et intitule a y inscrire."
}
```

The `description` is not decoration: the Standard Module Structure asks that "all
variables and outputs should have one or two sentence descriptions", and it is the
only thing tooling can **extract** to document the module.

## Keep the tree flat

Last anti-pattern, the quietest: the module that calls a module that calls a
module. The official recommendation is blunt, "we strongly recommend keeping the
module tree flat, with only one level of child modules". Relations run through
**expressions** between calls, not through floors.

## Your turn

You know what Terraform sees of a refactoring, how to declare a move to it, which
witness to pick to prove nothing was destroyed, and what a `moved` will never fix.
The challenge hands you an **already applied** project, to refactor without losing
a single token.

```bash
dsoxlab run modules-module-anti-patterns
dsoxlab check modules-module-anti-patterns
dsoxlab hint modules-module-anti-patterns
```

It runs **offline**.

Target exam sub-objective: **4d** (refactor an existing configuration into modules).

Reference: [module anti-patterns](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/anti-patterns-modules/)
