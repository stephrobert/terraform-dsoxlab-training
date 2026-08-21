# The style guide: what CI checks, and why

A style guide is not something you re-read, it is something a **CI rejects**.
File names change nothing in Terraform's behavior, so checking them proves
nothing; what proves is the exit code of `terraform fmt -check` and the JSON of
`terraform validate`. This tutorial walks the official rules on **generic**
examples; the challenge makes you take a degraded configuration and bring it into
compliance.

## File naming, and its exceptions

Terraform **concatenates all `.tf`** files in a directory: the split is a
readability convention with no technical effect... with two exceptions. The
official style guide recommends:

- **`terraform.tf`**: the `terraform` block (`required_version`,
  `required_providers`). Note the official name is `terraform.tf`, not
  `versions.tf`.
- **`providers.tf`**: all `provider` blocks.
- **`variables.tf`**: all variables, **in alphabetical order**.
- **`main.tf`**: resources and data sources.
- **`outputs.tf`**: all outputs, **in alphabetical order**.

The two exceptions where the name **does** matter: `*_override.tf` (and
`override.tf`) files are loaded **last** and merged on top; and a published
module repository must be named `terraform-<PROVIDER>-<NAME>`.

## Naming a resource

A resource is named with a **descriptive snake_case name**, without repeating the
type the address already carries:

```hcl
# good: the address is random_pet.serveur
resource "random_pet" "serveur" {}

# bad: camelCase, and the name repeats the type
resource "random_pet" "randomPetServeur" {}
```

The name `this` for a module's single resource is a widespread **community**
convention, but the official style guide never mentions it: it only asks for a
descriptive name.

## Ordering within a file, and within a resource

Two official orderings are often reversed. First, **dependent resources are
declared AFTER the ones they reference** ("let your code build on itself"), and
**a data source before the resource that consumes it**.

Then, inside a `resource` block, the parameter order is:

1. `count` or `for_each` (if present);
2. the resource's non-block arguments;
3. block-type arguments;
4. a `lifecycle` block (if needed);
5. **`depends_on` LAST** (if needed).

Many guides place `depends_on` at the top with the other meta-arguments: that is
the opposite of the official rule.

## Comments: # is idiomatic

HCL accepts `#`, `//` and `/* */`, but the docs are clear: **only `#` is
idiomatic**, for single- and multi-line comments. "The `//` and `/* */` comment
syntaxes are not considered idiomatic." The other two survive only for backward
compatibility.

## Type variables AND outputs

Since Terraform 1.15, the style guide asks for a **`type`** and a
**`description`** on each **output**, like for variables. The type is not
cosmetic: it documents the contract and corrects values. An output
`type = number` whose value comes from a `terraform.tfvars` writing it `"3"`
(quoted) comes out as a **number**:

```hcl
output "nombre_noeuds" {
  type        = number
  description = "Number of nodes."
  value       = var.nombre_noeuds
}
```

The official parameter order is `type`, `description`, `default`, `sensitive`,
`validation` for a variable; `type`, `description`, `value`, `sensitive` for an
output.

## Format and validate, before CI

Two commands, two distinct roles:

- **`terraform fmt`** normalizes indentation, aligns `=`, spaces inline maps.
  `terraform fmt -check` exits with **code 3** (not 1) when a file is not
  formatted.
- **`terraform validate`** checks internal consistency and **types**, but does
  **not** validate values against the provider and does **not** evaluate state.

Linting goes further: Terraform has no built-in linter; the docs recommend
**TFLint**. And the right place to run `fmt` and `validate` is a Git
**pre-commit hook**, where the error is cheapest to fix, before CI.

## The .gitignore: state out, lock in

This is the only style-guide rule whose omission has immediate security
consequences. You **never commit**: the `.terraform/` directory,
`terraform.tfstate*` files, `.terraform.tfstate.lock.info`, plans saved with
`-out`, and any sensitive `.tfvars`. You **do commit**
**`.terraform.lock.hcl`**, the provider version lock file.

<Aside type="caution" title="The .terraform* trap">
Ignoring the directory with `.terraform/` (with the slash) is correct. Writing
`.terraform*` (with the star) **also** ignores `.terraform.lock.hcl`, which must
be committed. The trailing slash restricts the pattern to the directory.
</Aside>

## Your turn

```bash
dsoxlab run write-code-style-guide
dsoxlab check write-code-style-guide
dsoxlab hint write-code-style-guide
```

Exam objectives: **2a** (validate the configuration) and **2e** (typing
variables and outputs).

Reference: [The Terraform style guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/style-guide-terraform/)
