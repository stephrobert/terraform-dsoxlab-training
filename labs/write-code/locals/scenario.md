# Scenario: the local that is not computed at plan time

**Exam objective targeted: 2c (use built-in HCL functions and expressions), with a deliberate spill into 2f for sensitivity propagation.**

A local is not a variable: nothing overrides it from outside, it accepts neither type nor description, and its value is not always known at plan time. The learner must build a chain of locals crossing those three traps and prove it without ever reopening a `.tf` file.

## Capability targeted

Centralise a configuration's expressions in `locals` blocks: normalising identifiers with HCL functions, typed conditional computation, generating a list with a `for` expression, deriving from a resource attribute, and assembling a value inheriting a variable's sensitivity. Be able to say, for each local, whether it resolves at plan time or only at apply time, and why.

## Where the learner starts

`challenge/work/` holds an incomplete project. No VM, no remote account: only `hashicorp/local` and `hashicorp/random` are used, with a `terraform init` and a `.terraform.lock.hcl` already in place. The lab runs anywhere `terraform` is on the PATH, without network access.

The directory holds `versions.tf` and `variables.tf` (already correct), `locals.tf`, `main.tf` and `outputs.tf`. The supplied variables are `project` (value `Atelier_Locaux`), `environment`, `node_count`, `memory_mb` and `db_password`, the last one declared `sensitive = true`. `locals.tf` arrives with **three separate `locals` blocks**, deliberately, so that the learner observes Terraform merging them. All their content is holed:

```hcl
locals {                      # naming
  slug      = ???             # project lowercased, underscores turned into dashes
  base_name = ???             # slug and environment joined by a dash
}

locals {                      # computation
  is_production   = ???       # true only if environment is prod
  effective_ram   = ???       # memory doubled in prod, otherwise the variable's value
  node_names      = ???       # base_name suffixed -001, -002, ... over node_count
}
locals {                      # derived from a resource, hence unknown at plan time
  build_digest  = ???         # first 8 characters of random_id.build.hex
  manifest_name = ???         # base_name, dash, build_digest, .json extension
  db_dsn        = ???         # a postgres DSN built from db_password and base_name
}
```

`main.tf` already declares `random_id.build` and a `local_file.manifest` whose `filename` and `content` point at locals that do not exist. `terraform plan` fails as it stands.

## The state to reach

1. `base_name` is `atelier-locaux-prod`: the case and the underscore of `Atelier_Locaux` have been normalised, and one local references another within the same block.
2. `node_names` is a list of `node_count` strings of the form `atelier-locaux-prod-001`, numbered on three digits. It consumes a local declared in another block, which proves the blocks merge.
3. `effective_ram` is a JSON **number**, never a string. In `prod` it is twice the variable, elsewhere its exact value. The trap is that Terraform converts a ternary's two branches to a common type without complaining: writing `4096 : "2048"` produces a valid configuration and a string-typed result.
4. `manifest_name` is `atelier-locaux-prod-<8 hexadecimal characters>.json`, those eight characters really being the prefix of `random_id.build.hex`.
5. Before the apply, on an empty state, the output exposing `manifest_name` is announced as unknown: a local derived from a resource attribute does not resolve at plan time.
6. `db_dsn` inherits `var.db_password`'s sensitivity: the output exposing it is marked sensitive, failing which Terraform refuses to run.
7. `local_file.manifest` exists, its path is `manifest_name` and its content is JSON carrying `base_name`, the node list and the computed memory.
8. The project converges: a second plan right after the apply proposes nothing.

## How it is proven

The tests never open the learner's `.tf` files and parse no human output. They run Terraform inside `challenge/work` and read only JSON or exit codes.

1. `terraform plan -out=tfplan` on an empty state, then `terraform show -json tfplan`: in `output_changes`, the `manifest_name` entry carries `after_unknown` as true, while `base_name` already carries its final value. The boundary between plan and apply is proven by the same document.
2. `terraform apply -auto-approve` then `terraform output -json`: `base_name` is exactly `atelier-locaux-prod`, which cannot come out of `Atelier_Locaux` without normalisation.
3. Still in that JSON, `node_names` is a list of length `node_count` whose every element is matched against the `atelier-locaux-prod-\d{3}` pattern, element by element.
4. `effective_ram` is checked by its **JSON type** before its value: a number, never a string. The lab is replayed with `-var environment=dev` and the double check, type then value, is done again.
5. `terraform show -json`: a resource of `mode: managed` and type `random_id` exposes `hex`, and the `local_file`'s `filename` starts with `atelier-locaux-prod-` followed by the first eight characters of that `hex`. Both values are compared within the same document, never copied by hand.
6. In that same `terraform show -json`, `values.outputs.db_dsn.sensitive` is true. A configuration whose output was not marked sensitive would not have reached the apply anyway.
7. The `local_file`'s content is read back through the JSON's `content` attribute, deserialised, and its three keys are matched against the corresponding outputs.
8. `terraform plan -detailed-exitcode` returns 0 right after the apply. A code 2 fails the lab.
