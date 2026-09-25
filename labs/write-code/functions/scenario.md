# Scenario: compose values with HCL functions

**Exam objective targeted: 2c.**

HCL functions look like the easy part of the exam, until the day an out-of-range index, a missing key or a badly escaped template makes the plan fail. This lab chains those traps and adds the novelty almost no guide covers: the functions a provider exposes.

## Capability targeted

Produce the exact values resources and outputs expect while writing nothing but function expressions: normalise a string, deduplicate a collection to feed a `for_each`, merge maps with the right priority, render a template without corrupting its literal content, and call a function supplied by a declared provider.

## Where the learner starts

`challenge/work` holds a configuration that refuses to validate:

- `versions.tf`: `required_version = ">= 1.8"` and a `required_providers` block declaring only `local`. The built-in `terraform` provider (`source = "terraform.io/builtin/terraform"`) is not there.
- `variables.tf`, complete and not modifiable: `environments_csv = "prod,dev,prod,staging"`, `tags = { projet = "demo", equipe = "devops" }`, `environment = "qa"`, `memory_mib = 1536`.
- `locals.tf`: seven locals whose value is replaced by `???`.
- `outputs.tf`, complete and not modifiable: it exposes each of those locals.
- `main.tf`: one `local_file` resource per distinct environment, whose `for_each` and `content` are also holed with `???`.
- `templates/node.yaml.tftpl`: a template holding a marker to substitute, a `${...}` sequence to keep literal, and the `$HOME` and `$(date)` strings of a shell script.

## The state to reach

1. `terraform apply` completes without error, then `terraform plan -detailed-exitcode` returns 0.
2. State holds exactly three `local_file` instances, addressed by an environment value (`["dev"]`, `["prod"]`, `["staging"]`) and not by a numeric index: the `for_each` source is therefore a deduplicated collection, not the raw list from splitting the CSV.
3. The `env_recycle` output is `"staging"`: it is a positional access, over the sorted list of three environments, with an index of 5. The index wraps around modulo and therefore does not fall back on the first element.
4. The `taille` output is `"small"` although `"qa"` is absent from the lookup table: the read supplies a fallback value instead of interrupting the plan.
5. The `tags_effectifs` output holds `projet`, `equipe` and `env`, and `env` is `"qa"`: the map added last prevails.
6. The `memory_gib` output is `2` for 1536 MiB: rounding goes up, never down.
7. Every file written to disk holds the substituted hostname, the `${...}` sequence left literal, and `$HOME` as well as `$(date)` intact.
8. The `tfvars_rendu` output is produced by `provider::terraform::encode_tfvars`, which presupposes having declared the built-in `terraform` provider in `required_providers` and re-run `terraform init`.

## How it is proven

- `terraform output -json` supplies the six expected scalar values. A miscomputed positional access, a map read without a fallback, a merge in the wrong order or rounding down all change the value and fail the corresponding test.
- `terraform show -json` gives the resource list: filter on `mode == "managed"` and `type == "local_file"`, then check the set of `index` values is exactly `{"dev", "prod", "staging"}`. A `for_each` over the non-deduplicated list fails at apply time, a `count` produces integer indices, and both are detected here.
- The same document exposes each instance's `content` attribute: the test looks there for the substituted hostname, the literal presence of `${`, and that of `$HOME` and `$(date)`. Escaping every `$` as `$$`, as many tutorials suggest, leaves `$$HOME` in the rendering and fails.
- The `tfvars_rendu` output proves the provider function was called: the test compares the exact string the encoding produces, and that value stays unavailable while the built-in provider is not declared.
- `terraform plan -detailed-exitcode` must return 0 after the apply. Code 2 signals an unstable expression, typically a timestamp slipped into the template.
- No test reads the learner's `.tf` files. A `challenge/work` left as it stands produces neither state nor output: the first command fails and nothing passes.
