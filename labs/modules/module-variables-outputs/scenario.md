# Scenario: a module interface is a contract

**Target exam sub-objective: 2e (variables and outputs, complex types), supporting 4a (create a module) and 2f (sensitive data).**

A module is judged by what it accepts as input and what it guarantees as output.
This lab tackles four traps that the `type` plus `default` pair does not cover:
an optional object attribute, an explicitly passed `null`, an output that must
refuse to publish itself, and a re-exported secret that fails the plan until it
is marked.

## Target capability

Design the interface of a reusable module: make an object attribute optional with
`optional()` rather than multiplying variables, shield a variable against an
explicit `null`, reject an out-of-range value with an actionable message, gate an
output behind a `precondition`, and correctly re-export a sensitive value coming
from the child module.

## Where the learner starts

`challenge/work/` holds an incomplete Terraform project. No VM, no remote
account: only `hashicorp/local` and `hashicorp/random` are used, and the lab runs
anywhere `terraform` 1.15 or later is on the PATH, offline.

Already correct and not to be touched: `versions.tf`, the child module's
`main.tf` under `modules/artefact/` (it creates `random_password.this` of length
`var.longueur_secret` and `local_file.this` whose name derives from
`var.depot.nom`), and the root `main.tf`, which calls the module twice:
`module "complet"` provides every attribute, `module "minimal"` provides only
`depot = { nom = "livraison" }`.

Three files are holed. `modules/artefact/variables.tf` must declare `depot` (an
object whose `nom` is required, `retention_jours` defaults to 7 and `chiffre`
defaults to true), `etiquette` (string, default `"artefact"`, where an explicit
null must still yield the default) and `longueur_secret` (number, default 16,
refused outside 12 to 64). `modules/artefact/outputs.tf` must expose `resume`,
`secret` and `chemin`, the last one published only when the repository is
encrypted. The root `outputs.tf` exposes `resume_minimal` and `secret_partage`.
As shipped, the `???` are not valid HCL and nothing plans.

## The state to reach

1. The work really lives in a module called twice, not duplicated at the root.
2. The minimal call succeeds without providing `retention_jours` or `chiffre`:
   the module contract fills the gaps with 7 and `true`.
3. A call passing `etiquette = null` still gets `"artefact"`: the variable
   refuses null instead of propagating it.
4. `longueur_secret = 8` is rejected before anything is created, with a message
   naming the bounds.
5. The secret produced by the module has exactly the requested length and reaches
   the root without being readable in ordinary output.
6. The `chemin` output refuses to publish itself when the repository is not
   encrypted, and the plan stops there.
7. The project converges: a second plan right after the apply proposes nothing.

## How it is proven

Tests never open the learner's `.tf` files and never parse human-facing output.
They run Terraform inside `challenge/work` and read only JSON or exit codes.
Faulty variants are produced in temporary copies of the project, never in `work`.

1. `terraform show -json`: `values.root_module.child_modules` holds two entries,
   `module.complet` and `module.minimal`. A flat configuration fails here.
2. `terraform output -json`: `resume_minimal` is exactly
   `{"nom": "livraison", "retention_jours": 7, "chiffre": true, "etiquette": "artefact"}`,
   while the call only provides `nom`. Only `optional(type, default)` produces
   that result: without it the plan would fail on an incomplete object, and with
   an `optional()` lacking its second argument both fields would come out `null`.
3. A copy where the minimal call receives `etiquette = null`: after apply,
   `resume_minimal.etiquette` is still `"artefact"`. Without `nullable = false`,
   that JSON holds `null`, a behaviour verified on 1.15.4.
4. A copy where `module "complet"` receives `longueur_secret = 8`:
   `terraform validate -json` returns `"valid": false` and an `error` diagnostic
   whose `summary` is `Invalid value for variable`.
5. `terraform output -json`: `secret_partage` carries `"sensitive": true` and its
   value has the expected length. A control test removes that marking in a copy
   and checks that `terraform plan` then exits non-zero: sensitivity travels up
   from the child module, and an unmarked root output is refused.
6. A copy where `module "complet"` receives `chiffre = false`: the plan fails
   with a diagnostic reporting a failed precondition on a module output, and the
   exit code is non-zero. Without the `precondition`, that plan would succeed.
7. `terraform plan -detailed-exitcode` returns 0 right after the apply. A code 2
   fails the lab.
