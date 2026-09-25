# Scenario: a module does not configure its providers

**Exam objective targeted: 4a.**

A child module carrying its own `provider` block works as long as you call it once, and breaks the moment you give it a `for_each`. That is the trap covered here: the official rule, "a module intended to be called by one or more other modules must not contain any `provider` blocks", is almost never discovered by reading the documentation, but by hitting Terraform's refusal.

## Capability targeted

Write a reusable child module: empty it of every provider configuration while keeping its own `required_providers`, have it declare through `configuration_aliases` the aliased configuration it expects, pass that configuration to it from the root through the `providers` argument, and instantiate the module as many times as needed from a single block carrying `for_each`.

## Where the learner starts

`challenge/work` holds neither state nor `.terraform`. No cloud account: only `hashicorp/local`, `hashicorp/random` and `hashicorp/tls` are used, all three offline once installed.

**The choice of `tls` is not decorative, it is imposed by measurement.** Terraform's refusal only fires if the child module carries a **genuinely configurable** provider configuration. Verified on 1.15.4: with `local`, `random` or `null`, which accept no argument, a `provider` block in a child called with `for_each` produces only a **warning**, `Redundant empty provider block`, and `validate` stays green. With `tls`, whose `proxy` block is a real configuration, the call fails at `init` time.

- `versions.tf` (root): complete, not to be touched. `required_version = ">= 1.15.0"`, the three providers pinned, one default `provider "local" {}` configuration and a second `provider "local" { alias = "archive" }`.
- `variables.tf` (root): complete. `environnements`, a `map(object({ cible = string, retention = number }))` with three entries: `dev`, `preprod`, `prod`.
- `main.tf` (root): a single `module "livrable"` block with `source = "./modules/livrable"` and `for_each = var.environnements`. Its arguments are holed with `???`, and it carries no `providers` argument.
- `outputs.tf` (root): `empreintes` and `chemins_archives` started, values holed.
- `modules/livrable/versions.tf`: a `required_providers` block that does declare `local`, `null` and `random`, but whose `configuration_aliases` line is holed with `???`.
- `modules/livrable/main.tf`: at the top, a `provider "local" {}` block inherited from an old copy-paste. Then `random_pet.etiquette`, `local_file.manifeste`, `local_file.archive` (which already carries `provider = local.archive`) and `null_resource.scellement`.
- `modules/livrable/variables.tf`: `nom`, `cible` and `retention` declared with their `type`, but with no `description`.
- `modules/livrable/outputs.tf`: `empreinte` and `chemin_archive` started, values holed, with no `description`.

The brief requires an `init` before any modification, and **it is the init itself that refuses**, before any `validate`:

```text
Error: Module is incompatible with count, for_each, and depends_on

The module at module.livrable is a legacy module which contains its own local
provider configurations, and so calls to it may not use the count, for_each,
or depends_on arguments.

If you also control the module "./modules/livrable", consider updating this
module to instead expect provider configurations to be passed by its caller.
```

The message states the problem **and** the solution. Once the provider configuration is removed from the child, two refusals follow one another, each naming the next step: `Provider configuration not present` while the module references `local.archive` without having declared it, then `Missing required provider configuration` while the caller does not pass it.

## The state to reach

1. No provider configuration lives anywhere but in the root module: the `provider "local"` block is gone from `modules/livrable/`.
2. The module keeps its three `required_providers`: configurations are inherited, source and version requirements never are.
3. `modules/livrable/versions.tf` declares `configuration_aliases = [local.archive]` under its `local` requirement.
4. The root's `module "livrable"` block carries a `providers` argument mapping the root's aliased configuration to the name the child expects, `local.archive = local.archive`. The other configurations stay **inherited** without writing anything: measured on 1.15.4, a partial `providers` does not cancel the inheritance of the configurations it does not name, and `local_file.manifeste` does stay attached to the default `local` configuration. Passing `local = local` explicitly is a matter of clarity, not a technical requirement.
5. `for_each` produces three instances, `module.livrable["dev"]`, `["preprod"]` and `["prod"]`, whose arguments are wired from `each.key` and `each.value`.
6. Inside the module, `local_file.archive` is attached to the aliased configuration, the three other resources to the default one.
7. Every variable and every output of the module carries a non-empty `description`; `nom` and `cible` have no `default` and therefore stay mandatory.
8. The root's two outputs aggregate the three instances' outputs, indexed by environment name.
9. An `apply` goes through end to end, the three environments' files exist, and a `plan` right afterwards proposes nothing.

## How it is proven

The tests drive Terraform and never read the `.tf` files.

- `terraform plan -out=tfplan` then `terraform show -json tfplan`, the `configuration.provider_config` table: it holds an entry with `alias` `archive` for `local`, and **no** entry whose `module_address` names `module.livrable`. No provider configuration lives in the child. The mere existence of that plan already proves the point, since `init` fails while the child configures a provider and the call carries `for_each`.
- Same document, `configuration.root_module.module_calls.livrable`: the **`for_each_expression`** key is present, at the top level. Careful, it does **not** live under `expressions`, which only carries the module's arguments; and the JSON exposes **no** `providers` key, so the argument has to be proven another way.
- Same document, `configuration.root_module.module_calls.livrable.module.resources`: the `provider_config_key` of `local_file.archive` is `local.archive`, that of `local_file.manifeste` is `local`. Two configurations of the same provider coexist within a single module, and **that field is what proves the `providers` argument is wired**, since the JSON does not expose it directly.
- Same document, `...module_calls.livrable.module.variables`: every variable has a non-empty `description`, and neither `nom` nor `cible` carries a `default` key. Likewise on `...module.outputs` for descriptions.
- The plan's `resource_changes`: twelve entries, all in `mode: "managed"`, whose addresses start with `module.livrable["dev"]`, `module.livrable["preprod"]` and `module.livrable["prod"]`. A single `module` block produces three instances.
- After the apply, `terraform show -json`: `values.root_module.child_modules` counts three entries whose `address` are the three indexed addresses.
- `terraform output -json`: `empreintes` and `chemins_archives` are objects with exactly three keys, and every announced path corresponds to a file actually present on disk.
- `terraform plan -detailed-exitcode`: code 0 right after the final apply.

None of these checks passes on an empty directory, nor on the starting configuration, whose `validate` fails.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/creation-modules/
