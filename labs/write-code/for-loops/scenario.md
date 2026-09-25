# Scenario: transform a server catalogue with for expressions

**Exam objective targeted: 2c.**

A `for` expression returns a tuple between brackets and an object between braces,
and a `[*]` splat on a map raises no error: it wraps the whole map in a
single-element tuple. This lab covers both traps.

## Capability targeted

Derive, from a single map of servers and without ever duplicating a source datum,
the four collections the configuration requires: a filtered list, an object
grouped by role, a flattened crossing of two levels, and a set feeding a real
resource's `for_each`.

## Where the learner starts

`challenge/work` holds a `local` and `null` configuration already initialised
(`terraform init` run, no `apply`, no state):

- `variables.tf`: `var.serveurs`, a `map(object({ env, role, memoire_mo,
  actif, tags }))` of six entries with default values. Not to be modified.
- `locals.tf`: four `locals` whose expression body is `???`.
- `main.tf`: a `local_file.fiche` resource whose `for_each` is `???`, the file's
  content being already written.
- `outputs.tf`: four `output` blocks exposing the `locals`, already written, not
  to be modified.

Two servers share a role, one `prod` server is inactive, one server has an empty
tag list: every shortcut shows.

## The state to reach

1. `output "noms_prod"`: a tuple of the names of servers whose `env` is `prod`,
   in the lexicographic key order Terraform imposes by itself.
2. `output "par_role"`: an object where each key is a role and each value the
   list of names carrying that role. Shared roles must group, not overwrite the
   key.
3. `output "memoires"`: a tuple of six numbers, one entry per server. Six, not
   one: a tuple of length 1 signs a splat applied to the map.
4. `output "tags_plats"`: a tuple of `"<server>:<tag>"` strings, one per existing
   pair. The server with no tag does not appear in it.
5. A `local_file` exists for every server that is both `prod` and `actif`, and
   for no other: the resource's instance keys are exactly that set.
6. A second apply proposes no change.

## How it is proven

The tests decode `terraform output -json`: the root's type (a list for tuples, a
dictionary for the grouped object), the exact length, the expected content. The
length of 6 on `memoires` catches the splat; a list-typed value under each key of
`par_role` proves the ellipsis; the absence of the tagless server from
`tags_plats` proves the flattening rather than a hand-made concatenation.

`terraform show -json` supplies `values.root_module.resources`: the tests keep
the entries with `mode == "managed"` and `type == "local_file"`, then compare the
set of their `index` values with the expected servers. An unfiltered `for_each`
produces six instances and fails. Finally `terraform plan -detailed-exitcode`
must return 0. No test reads a `.tf` file.
