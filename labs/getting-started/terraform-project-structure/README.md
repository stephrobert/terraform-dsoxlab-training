# Split a monolith without moving the plan

Terraform evaluates **every** `.tf` file in a directory as a single document.
File names and their order have no functional effect: they are reading
conventions, not instructions.

The direct consequence, and the whole lab: splitting a monolith must produce
**exactly the same plan**. What is proven is not the presence of well-named
files, it is invariance.

## The conventional split

| File | What it carries |
| --- | --- |
| `terraform.tf` | the `terraform` block, required versions and providers |
| `providers.tf` | provider configurations |
| `variables.tf` | the inputs |
| `locals.tf` | computed values |
| `main.tf` | the resources |
| `outputs.tf` | the outputs |

Nothing mandates those names. They are worth using because the whole team knows
where to look.

## Splitting means moving

Copying instead of moving declares every name **twice**, and Terraform refuses:

```text
Error: Duplicate variable declaration
Error: Duplicate resource "local_file" configuration
```

A name is declared once per **directory**, whichever file carries it. It is the
same rule that makes file order irrelevant: there is only one namespace.

## The only proof worth having: compare two plans

```bash
terraform plan -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | {address, actions: .change.actions}'
```

A well-named file proves nothing. Two identical plans do.

The lab rebuilds the monolith's plan from a supplied reference copy, rather than
trusting a plan you froze yourself: nothing would force the latter to have been
taken **before** the split.

## What `show -json` does not tell you

Measured while writing this lab, and it changed its design: **the JSON plan
exposes no source position**. Neither `configuration.root_module.resources` nor
the variables say which file they come from.

Proving "the variables are in `variables.tf`" without opening a `.tf` therefore
needs something else: **ablation**. Remove the file in a copy, and see what
breaks. Without `variables.tf`, `validate` refuses. Without `main.tf`, the plan
carries no resource at all.

That is a proof about behaviour, not about text.

## Precedence, and the rung everyone places too high

The lab has the same variable set by several sources at once:

```text
default  <  TF_VAR_  <  terraform.tfvars  <  *.auto.tfvars  <  -var
```

The decisive rung is the second: a plain values file **beats** the environment
variable. `TF_VAR_` lives just above the `default`, and below **every** file.

The most discreet is the third: a `*.auto.tfvars` is loaded automatically, after
`terraform.tfvars`. Its name does not say so, no command mentions it, and the
colleague who drops one changes everybody's behaviour.

## Over to you

```bash
dsoxlab run getting-started-terraform-project-structure
dsoxlab check getting-started-terraform-project-structure
dsoxlab hint getting-started-terraform-project-structure
```

It runs **offline**, on `local`, `null` and `random`.

Nine tests. Three of them carry a guard refusing to measure anything while the
monolith is still there: without it they were green before any work, since the
monolith already produces a plan identical to itself.

Exam objective targeted: **2e**, supported by **2a**.

Reference: [structuring a Terraform project](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/structure-projet-terraform/)
