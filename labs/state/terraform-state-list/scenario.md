# Scenario: the address is the identity in the state

**Target exam objective: 1e.**

A lab that merely lists proves nothing. This one tackles the real subject of
`terraform state list`: the address is an instance's only name in the state, and
the trap is believing that an address designates a single resource, that a `grep`
replaces native filtering, and that modules behave like the root.

## Target capability

Find, in a state, the exact address of an instance when all you know is its real
identifier, whether it is indexed by position, indexed by key or lodged in a
module, and count the managed resources of a modularised configuration without
getting the number wrong.

## Where the learner starts

`challenge/work` holds neither state nor `.terraform`. Every file is complete,
applicable as is and off limits, except one:

- `versions.tf`: `required_version = ">= 1.15.0"`, providers `hashicorp/local`
  and `hashicorp/random` pinned.
- `main.tf`: `random_pet.worker` with `count = 6`, `random_pet.service` with
  `for_each` over eight keys, `local_file.journal`, and a `local_file` data
  source. Three **seeded** `random_integer` resources designate a rank, a key and
  an archive; `locals` use them to point at one instance of each family. The seed
  makes the draw **reproducible across machines**, which is what allows a
  replayable reference solution, but it writes the result nowhere: to know which
  instance carries the published identifier, you must query the state.
- `modules/stockage/`: `random_pet.archive` with `for_each` over five keys, a
  `local_file` and a `local_file` data source. This module exists for one reason:
  half the command's traps only appear under a module. It ships as a fixture in a
  **subdirectory**, which the shell runtime only supports from **dsoxlab 0.1.37**
  onwards: before that, its `main.tf` overwrote the root one.
- `outputs.tf`: three outputs `id_worker_recherche`, `id_service_recherche` and
  `id_archive_recherche` expose the **identifier value** of the designated
  instances, never their address. Five more outputs simply return the answer
  variables.
- `reponses.auto.tfvars`: **the only file to fill in**, five `???`.

The statement therefore imposes an `init` then an `apply` first: the identifiers
are generated at run time, they are neither in the files nor guessable.

## Target state

1. The configuration is applied: the state holds 6 `random_pet.worker` instances,
   8 `random_pet.service` instances, 5 `module.stockage.random_pet.archive`
   instances, both managed `local_file` resources and both data sources.
2. `adresse_worker` is the full address of the `random_pet.worker` instance whose
   `id` is the one published by `id_worker_recherche`, in its position-indexed
   form, brackets included.
3. `adresse_service` likewise, for the matching `random_pet.service` instance, in
   its key-indexed form, quotes included.
4. `adresse_archive` is the **module-qualified** address of the matching
   `random_pet.archive` instance, `module.stockage.` prefix included.
5. `adresse_data_module` is the full address of the data source declared in
   `modules/stockage/`, the one that does not start with `data` even though it is
   one.
6. `nombre_managees` is the exact number of `mode: managed` resources in the
   state, modules included and data sources excluded.
7. A `plan` after the last `apply` proposes nothing: filling in the answers moved
   nothing.

## How it is proven

The tests drive Terraform and never read the learner's files.

- The test rebuilds the truth from `terraform show -json`, descending
  `values.root_module` then recursively `child_modules`: for each instance it
  holds the `address` and `values.id` pair, plus the `mode`. No human-facing
  output is parsed.
- `terraform output -json` supplies the three identifiers sought and the five
  answers. The test resolves each identifier to its address in the table it built,
  then compares character for character. An answer right about the resource but
  wrong about the index, the key or the module prefix fails.
- The odds rule out guessing: 6, 8 and 5 candidates, one chance in 240 of getting
  all three right blind. The three targets are, moreover, neither the first
  position nor the first key in alphabetical order, precisely so that "try the
  first one" is not a winning strategy. The `apply -replace` check that this
  scenario's first version contemplated was dropped: with a seeded draw a
  replacement gives back the same target, and without a seed no static reference
  solution would be replayable.
- `adresse_data_module` is compared with the state's single `mode: data` instance
  whose address contains `module.`. That is exactly the entry the
  `state list | grep -v ^data | wc -l` recipe wrongly counts as managed.
- `nombre_managees` is compared with the JSON count of `mode: managed`. A learner
  applying the `grep` recipe hands in a number one too high, and the test refuses
  it. The test also proves the gap is really there: without it, the lab would
  demonstrate nothing.
- The command's real behaviour is exercised too: an address without an index
  returns all instances, a module address is a valid filter, the output order
  follows module depth, the four distinct diagnostics all exit 1, and an `-id`
  with no match exits 0 with empty output.
- `terraform plan -detailed-exitcode` returns 0 right after the last `apply`.

None of these checks passes on an empty directory, nor on a state that was never
queried: the five answers can only come from `terraform state list`, its `-id`
option and its filtering addresses.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-list/
