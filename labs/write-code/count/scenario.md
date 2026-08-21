# Scenario: count indexes by position, and the position lies

**Exam objectives: 4b (Terraform Associate, count and for_each meta-arguments) and the Professional-level migration with a `moved` block.**

Both `count` and `for_each` create several instances of a resource, but one indexes them by a positional integer and the other by a key. That detail decides whether removing an element from the middle of a set recreates others. The learner must pick the right meta-argument for each resource and prove it without ever reopening a `.tf` file.

## Target capability

Tell, on a concrete case, when `count` fits (interchangeable instances, a number of copies, a 0/1 optional resource) and when `for_each` is required (instances with their own identity that adding or removing one must not shift). Expose the attribute of a conditional resource with `one()`, and read the JSON plan to prove a config change destroys only what it must.

## Where the learner starts

`challenge/work/` holds an incomplete project. No VM, no remote account: only `hashicorp/local` and `hashicorp/random` are used, with `terraform init` already in place. The lab runs anywhere `terraform` is on the PATH, offline.

The directory has `versions.tf` and `variables.tf` (already correct), `main.tf`, `workers.tf`, `rapport.tf` and `outputs.tf`. Variables are `services`, a `list(string)` of `["web", "api", "cache"]`, `workers`, a number defaulting to `3`, and `rapport`, a bool defaulting to `false`. `main.tf` ships the **applicable count version** of `local_file.service`, on purpose: the learner sees the trap live, then migrates it. `workers.tf`, `rapport.tf` and `outputs.tf` come with `???` holes. `terraform init` fails as-is.

## The state to reach

1. `local_file.service` is addressed by key: the state holds `local_file.service["web"]`, `["api"]`, `["cache"]`, never `[0]`, `[1]`, `[2]`. That requires `for_each = toset(var.services)` and `each.key`.
2. The migration from count to for_each destroys nothing: `moved` blocks link `service[0]` to `["web"]`, `[1]` to `["api"]`, `[2]` to `["cache"]`.
3. Removing a service from the middle only destroys that service. A replan with `services=["web","cache"]` marks only `service["api"]` as `["delete"]`; `web` and `cache` stay `no-op`. A `count` solution would fail here.
4. `random_pet.worker` stays on `count = var.workers`: three genuinely interchangeable instances, the one case where `count` is the right tool.
5. `local_file.rapport` carries `count = var.rapport ? 1 : 0` and does not exist by default.
6. Outputs are wired: `noms_workers` via the splat `random_pet.worker[*].id`, `chemins_services` via a `for` expression over the map (splat does not apply to `for_each`), `rapport` via `one(local_file.rapport[*].filename)`.
7. The project converges: a second plan right after apply proposes nothing.

## How it is proven

The tests drive Terraform and never assert on the content of the learner's `.tf` files. They read only JSON and return codes.

1. `terraform show -json` after apply: every `local_file.service` instance carries a **string** `index`, and the set of indices is `{web, api, cache}`. An integer index (a `count`) fails the test. `random_pet.worker` has three integer-indexed instances.
2. `terraform plan -var 'services=["web","cache"]'` then `terraform show -json`: the only `service` instance with `delete` is `local_file.service["api"]`; none carries `["delete","create"]` or `["create"]`.
3. Migration test: a temp dir is seeded with the frozen count version from `challenge/reference/`, applied to reach the "before" state, then overlaid with the learner's migrated config. Every `service` change must be `no-op` with a `previous_address` in `local_file.service[N]`. Without the `moved` blocks, the same plan reports three deletions and three creations.
4. `terraform plan -var 'workers=2'`: only `random_pet.worker[2]` is destroyed; reducing `count` drops the highest index.
5. `terraform output -json`: `noms_workers` is a list of three, `chemins_services` a map of three named keys, `rapport` is null. Then `plan -var 'rapport=true'`: a single planned creation, `local_file.rapport[0]`.
6. `terraform plan -detailed-exitcode` returns 0 right after apply.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/count-terraform/
