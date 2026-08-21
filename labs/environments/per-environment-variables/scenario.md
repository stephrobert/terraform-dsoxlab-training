# Scenario: the value that wins, and why

**Exam sub-objective covered: 2e.**

Splitting per-environment values across `.tfvars` files is easy; knowing which of
six competing sources ends up in the plan is much harder. This lab covers the
full precedence ladder, including the two rungs most tutorials miss: the
`TF_VAR_` environment variables, absent from published tables, and the fact that
`-var` and `-var-file` sit at the **same** rank, settled by argument order rather
than by any hierarchy.

## Target capability

Parameterise a single configuration for three environments using value files,
then predict and demonstrate, for a given variable, which source prevails among
the `default`, an environment variable, `terraform.tfvars`, an `*.auto.tfvars`
and the command-line options.

## Where the learner starts

`challenge/work` holds a configuration that is neither initialised nor applied,
limited to the `hashicorp/local` and `hashicorp/random` providers:

- `versions.tf`: complete, leave it alone. `required_version = ">= 1.15.0"`, both
  providers pinned.
- `variables.tf`: `env_name` and `disk_size_gb` with no `default` (the guard
  rail), `retention_jours` with one, `base_image` and `tags` stubbed with `???`
  for their type.
- `main.tf`: `local_file.profil` writes a `jsonencode` of the resolved values to
  `profils/${var.env_name}.json`, and `random_pet.suffixe` carries the
  environment in its `keepers`. Both blocks are stubbed with `???`.
- `outputs.tf`: `profil` and `taille_octets` stubbed, expressions to be written.
- `terraform.tfvars` **present at the root**, carrying `env_name = "bac-a-sable"`
  and `disk_size_gb = 1`. It silently defeats the guard rail:
  `terraform plan -input=false` succeeds even though no environment was chosen.
  This is the starting observation, not a typo.
- `commun.auto.tfvars`: shared values (`base_image`, `tags`).
- `envs/dev.tfvars` complete, `envs/staging.tfvars` carrying a misspelled key
  (`disk_size_go`), `envs/prod.tfvars` incomplete.

## The state to reach

1. `terraform plan -input=false`, with no variable option, **fails** on
   `No value for required variable` for `env_name`: no implicit source supplies
   an environment value any more.
2. Genuinely shared values (base image, tags) stay auto-loaded, without being
   repeated across the three environment files.
3. `envs/staging.tfvars` no longer raises any undeclared-variable warning: the
   misspelled key is fixed, not worked around with a `default`.
4. All three environments deploy from the same configuration: dev at 4 GB and 7
   days of retention, staging at 4 GB and 14 days, prod at 8 GB and 90 days, each
   with its own profile file name.
5. With `TF_VAR_env_name` exported **and** `-var-file=envs/prod.tfvars`, the
   retained value is `prod`: an environment variable loses against a value file.
6. With `TF_VAR_env_name` exported alone, the retained value is the one from the
   environment: it beats the `default`.
7. `terraform plan -var 'disk_size_gb=16' -var-file=envs/prod.tfvars` keeps
   **8**, and `terraform plan -var-file=envs/prod.tfvars -var 'disk_size_gb=16'`
   keeps **16**. Same pair of options, two outcomes: order settles it.
8. A second auto-loaded file, lexically after `commun.auto.tfvars`, overrides it
   for the variable they share.
9. `tags` is a complex type, passable through `-var` with JSON syntax, and the
   override takes effect.
10. After applying prod, a fresh plan proposes nothing.

## How it is proven

The tests drive Terraform and never read the learner's `.tf` or `.tfvars` files.

- **Resolved values**: `terraform plan -out=tfplan` then
  `terraform show -json tfplan`; the `variables` key of the plan representation
  exposes the retained value for each root variable. It is the only admissible
  proof of precedence, and it needs no apply.
- **Guard rail**: `terraform plan -input=false` with no option returns a non-zero
  exit code and mentions `env_name`. On the starting state, the same call
  succeeds.
- **Undeclared variable**: a plan using `envs/staging.tfvars` no longer carries
  `Value for undeclared variable`. On the starting state, that warning exists.
- **`TF_VAR_` precedence**: the tests inject `TF_VAR_env_name` into the process
  environment and compare two plans, with and without `-var-file`.
- **Option order**: two successive plans with the same options in both orders,
  and two different `disk_size_gb` values in the plan JSON. A configuration
  hard-coding the size could not produce both.
- **Lexical order**: an auto-loaded file with a lexically greater name is added
  to a copy of the work, and the shared variable is read back from the plan JSON.
- **Applied state**: `terraform show -json`; `local_file.profil` carries a
  `filename` bearing the environment name, and its `content` parses as JSON so
  the resolved values can be compared. Outputs confirm `profil` and
  `taille_octets`.
- **Idempotence**: `terraform plan -detailed-exitcode` returns 0 right after the
  prod apply.

None of these checks passes on an empty `challenge/work`: the first plan finds
neither variables nor resources there.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/variables-par-environnement/
