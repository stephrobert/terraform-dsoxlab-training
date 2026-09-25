# Splitting a configuration is not proven by `validate`

Splitting a `main.tf` that has become unreadable is a Terraform repository's first
hygiene reflex. It is also the operation most often described as **risk-free**, on
the grounds that `terraform validate` passes afterwards. That guarantee does not
exist.

## What `validate` does not look at

The documentation bounds its scope unambiguously: "The `validate` command does not
check if argument values are valid for a specific provider, but it will verify that
they are the **correct type**. It does not evaluate any existing state."

In practice: a block **lost** in the copy-paste, a variable no longer coming from
the same file, a resource duplicated under another name all pass `validate` without
a word. Measured, on a split where one resource and its output disappeared:

```text
Success! The configuration is valid, but there were some validation warnings
```

The configuration is **valid**, and the plan bears no resemblance to the previous
one. The only check that proves invariance is **comparing two plans**.

```bash
# before the split
terraform plan -out=avant.tfplan && terraform show -json avant.tfplan > avant.json

# after
terraform plan -out=apres.tfplan && terraform show -json apres.tfplan > apres.json

diff <(jq -S '.planned_values, .resource_changes' avant.json) \
     <(jq -S '.planned_values, .resource_changes' apres.json)
```

The JSON's `configuration` section legitimately **changes**: it is the
representation of the code, which reflects the split. It is `planned_values`,
`resource_changes` and `output_changes` that must stay **identical**.

## The file layout, and the names that surprise

The official style guide names the files, and two of those names are not the ones
found everywhere:

| File | What it holds |
| --- | --- |
| `terraform.tf` | **one** `terraform` block, `required_version` and `required_providers` |
| `providers.tf` | **all** `provider` blocks, with "always include a default provider configuration" |
| `variables.tf` | all `variable` blocks, in **alphabetical order** |
| `outputs.tf` | all `output` blocks, in **alphabetical order** |
| `main.tf` | the `resource` **and** `data source` blocks |

The very common `versions.tf` name appears **nowhere** in the documentation. And
the `provider` block gets a file of its own, not a warm spot next to the
`terraform` block.

<Aside>None of this is enforced by Terraform: the engine loads **every** `.tf` in
a directory and treats them as a single document. That is precisely why following
the **published** convention beats following your own.</Aside>

## The exception that contradicts the rule

One family of names **does** have a functional effect: `override.tf`,
`override.tf.json` and any `_override.tf` file. Terraform loads them **last** and
**merges** their content over existing blocks. Such a file is therefore not a file
like the others, and it is not a "generated" file either: the style guide lists it
among the module's files.

## Formatting the whole tree

`terraform fmt -check` only looks at the **current directory**. On a multi-level
tree, it is a check that reassures without verifying anything.

```bash
terraform fmt -check -recursive
```

The documentation names the option for exactly this case: "The `terraform fmt`
command can use the `-recursive` flag for subdirectories." Without it, your
continuous integration stays **green** with badly formatted subdirectories.

## The `.gitignore`, and the saved-plan trap

Three families are **never** committed: the `.terraform/` directory, the state and
its backups, and **saved plans**. That last point hides the trap:

```bash
terraform plan -out=tfplan
```

That file has **no extension**. A `.gitignore` that only knows `*.tfplan` does not
catch it, and a saved plan holds the **resolved** values, secrets included.

Conversely, one file must **always** be versioned: `.terraform.lock.hcl`. It is
what guarantees the whole team uses the same provider versions.

A `.gitignore` is not verified by **reading** it, but by making it **work**:

```bash
git check-ignore -v projet/tfplan projet/terraform.tfstate
git check-ignore projet/.terraform.lock.hcl && echo "PROBLEM: the lock is ignored"
```

## Your turn

You know what `validate` does not cover, how to prove a split changed nothing,
which file names the documentation retains, why `-recursive` is indispensable, and
what a `.gitignore` must let through. The challenge hands you a monolithic
configuration to split, with the plan as judge.

```bash
dsoxlab run environments-organize-terraform-repo
dsoxlab check environments-organize-terraform-repo
dsoxlab hint environments-organize-terraform-repo
```

It runs **offline**.

Target exam sub-objective: **1b** (generate an execution plan).

Reference: [organising a Terraform repository](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/organiser-repo-terraform/)
