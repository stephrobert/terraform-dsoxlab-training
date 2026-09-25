# Extract a module without destroying what is running

The Professional's fourth objective is the refactoring one. Writing a module from
a blank page is easy. Extracting one from an **already applied** configuration,
without destroying anything, is not — and that is where the level is decided.

A refactor that destroys production is a failed refactor, even if the final state
is correct.

## The starting point: the same thing three times

Three services, nine resources, three values that change. Adding a fourth service
currently means copying nine more lines. That is exactly what a module exists to
remove.

## Changing address is not changing object

A resource is identified in state by its **address**. Going from
`random_pet.api_nom` to `module.service["api"].random_pet.nom` changes that
address. With nothing else, Terraform sees nine addresses disappear and nine
appear: it **destroys and recreates everything**.

The `moved` block declares the re-addressing:

```hcl
moved {
  from = random_pet.api_nom
  to   = module.service["api"].random_pet.nom
}
```

Three properties make it the right method, preferable to `terraform state mv`:
it is **versioned** with the code, **replayed automatically** by the whole team
and by CI, and **declarative**, so nobody has to remember a command.

The expected plan:

```console
$ terraform plan
  # local_file.api_config has moved to module.service["api"].local_file.config
  ...
Plan: 0 to add, 0 to change, 0 to destroy.
```

## An empty plan does not prove you destroyed nothing

That is the nuance giving this capstone its value. A configuration that had
destroyed then recreated everything **converges too**: its plan is empty, and its
final state is correct.

What tells them apart are the **identifiers**. The lab supplies the starting
state with its nine ids, and requires all of them to be found again, at the new
addresses. A recreated resource carries a different one.

## Two traps measured while writing this lab

**`version` only applies to registry modules.** On a local source, Terraform
refuses at `init` time:

```text
Error: Invalid registry module source address
you also set the argument "version", which applies only to registry modules.
```

Versioning a local module therefore goes through the repository carrying it, not
through that argument.

**A block with several arguments does not fit on one line.** The compact form
`moved { from = X  to = Y }` answers `The argument "to" is required`, a message
that says nothing about layout. It is only valid with **one** argument.

## The module configures no provider

A module meant to be called several times **must contain no `provider` block**:
the configurations are passed by its caller. With a `for_each`, Terraform refuses
outright.

It does keep its own `required_providers`: **configurations** are inherited,
source and version **requirements** never are.

## And a detail that would move the files

The module writes with `path.root`, not `path.module`. Otherwise the files would
end up in the module's subdirectory, and Terraform, seeing a different path,
would recreate them — exactly what the re-addressing was meant to avoid.

## Over to you

```bash
dsoxlab run certifications-professional-capstone4-modules
dsoxlab check certifications-professional-capstone4-modules
dsoxlab hint certifications-professional-capstone4-modules
```

Six tests, offline. Three carry a guard refusing to measure while the resources
do not live under a module: without it, the supplied starting state made them
green before any work.

Exam objective targeted: **4**, and above all **4d**.

Reference: [the Terraform Authoring and Operations Professional syllabus](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
