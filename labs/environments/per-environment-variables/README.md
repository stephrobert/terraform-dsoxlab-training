# Six sources, one winning value

Splitting per-environment values across `.tfvars` files is the easy part.
Knowing **which** of six competing sources actually lands in the plan is not,
and that is what decides what you ship.

## The ladder, measured on Terraform 1.15.4

Weakest to strongest. Every rung was checked by pitting two sources against each
other and reading the retained value from the plan JSON.

| Rank | Source | Loading |
| --- | --- | --- |
| 1 | the `default` in a `variable` block | implicit |
| 2 | `TF_VAR_<name>` environment variable | implicit |
| 3 | `terraform.tfvars` | automatic |
| 4 | `terraform.tfvars.json` | automatic |
| 5 | `*.auto.tfvars`, in **lexical** order | automatic |
| 6 | `-var` and `-var-file` | explicit |

Two rungs are missing from nearly every table published online.

## Trap 1: environment variables lose to any file

`TF_VAR_env_name` beats the `default`, but **loses** to any `terraform.tfvars`
sitting in the repository. A CI pipeline exporting its values through the
environment can therefore be silently overridden by a committed file.

```bash
export TF_VAR_valeur=ENVIRONNEMENT
terraform plan -out=tfplan
terraform show -json tfplan | jq -r '.variables.valeur.value'
```

```text
TFVARS
```

## Trap 2: `-var` does not "always" win

You will often read that `-var` overrides **every** other source. That is wrong.
`-var` and `-var-file` sit at the **same** rank, and the **argument order**
settles it:

```bash
terraform plan -var 'disk_size_gb=16' -var-file=envs/prod.tfvars   # keeps 8
terraform plan -var-file=envs/prod.tfvars -var 'disk_size_gb=16'   # keeps 16
```

Same pair of options, two outcomes. Nothing on screen reveals it: only the plan
JSON tells you.

## Lexical order, not alphabetical

Two auto-loaded files are ranked by the **bytes** of their names, not by an
intuitive alphabetical order:

```text
9-x.auto.tfvars    valeur = "NEUF"
10-x.auto.tfvars   valeur = "DIX"
```

**`NEUF`** wins, because `"10-x"` sorts before `"9-x"` lexically, so `9-x` is
applied last. Same story between `B.auto.tfvars` and `a.auto.tfvars`: `a` wins,
where a case-insensitive sort would have picked `B`.

## A misspelled key breaks nothing, and that is the problem

Three behaviours, depending on where the typo lives:

| Where | What Terraform does |
| --- | --- |
| `TF_VAR_nosuchvar` | **nothing at all**, silently |
| in a `.tfvars` file | `Warning: Value for undeclared variable`, the variable stays at its `default` |
| through `-var` | `Error: Value for undeclared variable`, exit code **1** |

So a `disk_size_go` instead of `disk_size_gb` in an environment file yields a
perfectly **valid** plan with the wrong size.

## The only check that settles it

Do not read the value off the screen, read the one Terraform **retained**:

```bash
terraform plan -out=tfplan -var-file=envs/prod.tfvars
terraform show -json tfplan | jq '.variables'
```

```json
{
  "disk_size_gb": { "value": 8 },
  "env_name": { "value": "prod" },
  "retention_jours": { "value": 90 }
}
```

A value passed through `-var` shows up as a **string** (`"16"`) even for a
`number` variable: the representation exposes the raw input, and Terraform then
converts it according to the declared `type`.

## Your turn

The challenge hands you a configuration serving three environments, with a
`terraform.tfvars` that defeats its own guard rail, types left as `???`, and a
misspelled key.

```bash
dsoxlab run environments-per-environment-variables
dsoxlab check environments-per-environment-variables
dsoxlab hint environments-per-environment-variables
```

It runs **offline**, on the `local` and `random` providers.

Exam sub-objective covered: **2e**.

Reference: [managing per-environment variables](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/variables-par-environnement/)
