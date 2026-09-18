# Scenario: prove Terraform / OpenTofu compatibility, and where it stops

**Exam sub-objective covered: 5b (provider configuration: sourcing and versioning), leaning on 3a (provider installation and versioning).**

"The two tools are compatible" is repeated everywhere, and nobody checks it. The
trap here is implicit sourcing: without an explicit `required_providers`, each
binary resolves its providers on its own default registry, and the announced
portability is only a bet.

The lab goes further than the claim, and that is its point: it makes the learner
observe that compatibility is **real on the state** and **false on the lock
file**.

## Target capability

Make a configuration portable between `terraform` and `tofu` by declaring the
source and version constraint of every provider, then show through the
structured state that the state, the outputs and the plan stay equivalent from
one binary to the other, while measuring what the second tool leaves behind.

## Where the learner starts

`challenge/work` holds a single file, `main.tf`, **provided and complete**: a
two-word `random_pet` resource, a `local_file` resource writing the pet
identifier into `rapport.txt`, a `null_resource` whose trigger depends on that
identifier, and a `nom_animal` output.

There is no `terraform {}` block, therefore no `required_providers`, no version
constraint, no named registry. There is no `.terraform/`, no state, no lock
file.

**This configuration does not apply as is**, and that is deliberate: the
`random_pet` resource designates its provider through an **alias**,
`random.principal`. As long as no `provider "random"` block carries that alias,
Terraform answers `Provider configuration not present`. The starting point can
therefore make no test pass before the work, which is the only way to guarantee
that a green test means something.

Both binaries are expected on the machine. The lab plays entirely with
`terraform`; `tofu` adds the cross demonstration and, if it is missing, the last
three checks are **explicitly skipped**, never counted as failures.

## The state to reach

1. A `versions.tf` file declares `required_version`, a `required_providers`
   block explicitly naming `source` and `version` for `random`, `local` and
   `null` with **pessimistic** constraints, and a `provider "random"` block
   carrying the expected alias.
2. The project is initialised then applied: the state holds exactly three
   managed resources, and `rapport.txt` exists with the pet value.
3. The `nom_animal` output equals the identifier recorded in the state.
4. Right after the apply, `plan -detailed-exitcode` exits with 0.
5. `tofu` picks up the **same state**, with no destruction and no recreation:
   its plan exits with 0 and its reading of `nom_animal` is identical.
6. `tofu` resolves the **same provider versions**, but on
   `registry.opentofu.org` and not `registry.terraform.io`.
7. After `tofu` has run, the lock file is **rewritten** on its registry, and
   `terraform` refuses to start again until an `init -upgrade` has happened.
   After that `init -upgrade`, the plan returns to 0: the round trip changed
   nothing.

## How it is proven

No test opens the `.tf` files written by the learner.

- **Constraints** are read from `.terraform.lock.hcl`, which nobody writes by
  hand. Careful: `constraints` is only recorded there when the entry is
  **created**. A learner who runs `terraform init` before writing their
  constraints keeps a lock without `constraints`, and nothing adds them later,
  not even an `init -upgrade`. The tests therefore rebuild the lock in a **copy**
  of the directory, which makes the measurement independent of the order in
  which the learner worked.
- **Sourcing** is read from `provider_selections`, returned by
  `<tool> version -json`: addresses there are fully qualified, and the registry
  prefix differs between the two tools.
- **State** is read from `show -json`, **outputs** from `output -json`, and the
  report is observed on disk then confronted with the state attributes.
- **Idempotence** is read from the exit code of `plan -detailed-exitcode`, never
  from a sentence.
- The **cross demonstration** happens on a copy of the working directory, for a
  precise reason: `tofu init` rewrites the lock, which would make the learner's
  `terraform` unusable until an `init -upgrade`. A test does not break what it
  measures.
