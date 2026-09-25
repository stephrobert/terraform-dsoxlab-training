# tfvars files: precedence and the undeclared variable

A **`.tfvars`** file provides values without touching the code. Two things trip
people up, and this lab tackles them: the exact **precedence order** when several
sources disagree, and the fate of an **undeclared variable**, which fails
differently depending on where it comes from. This tutorial shows them on a
throwaway example; the challenge makes you fix a silent typo.

## Auto-loading and precedence

Terraform loads **without an argument**: `terraform.tfvars`,
`terraform.tfvars.json`, and any `*.auto.tfvars(.json)`. When several sources
give the same variable, the order is fixed, weakest to strongest:

| Rank | Source |
|---|---|
| 1 | the block `default` |
| 2 | `TF_VAR_<name>` |
| 3 | `terraform.tfvars` |
| 4 | **`terraform.tfvars.json`** |
| 5 | `*.auto.tfvars` (lexical order) |
| 6 | `-var` / `-var-file` and HCP Terraform |

The often-missed point: **`terraform.tfvars.json` is a distinct level above
`terraform.tfvars`**. If both give the same variable, the JSON variant wins.

## The trap: the undeclared variable

Here is the most costly gap. A value assigned to a variable **with no matching
`variable` block** does **not** behave the same depending on its source:

- in a **file** `.tfvars`: a plain **warning**, the `plan` succeeds;
- via **`-var`**: an **error**, the `plan` fails;
- via **`TF_VAR_`**: **silently ignored**.

```hcl
# terraform.tfvars, with a typo
env  = "prod"
zoen = "eu-west-3"   # "zoen" instead of "zone": the real variable stays at default
```

```text
Warning: Value for undeclared variable
```

The plan **succeeds**, but `zone` keeps its default. You think you changed a
value, you did not. This is exactly the "false diagnostic during a plan" this
topic teaches to avoid: **read the warnings**.

## Your turn

```bash
dsoxlab run write-code-tfvars-files
dsoxlab check write-code-tfvars-files
dsoxlab hint write-code-tfvars-files
```

Exam objective: **2e** (configure input variables and outputs).

Reference: [tfvars files in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fichiers-tfvars/)
