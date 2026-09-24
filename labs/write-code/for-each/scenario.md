# Scenario: add an instance without destroying the others

**Exam objective targeted: 2d, meta-arguments.**

`for_each`'s real subject is not its syntax, it is what it avoids: with `count`,
inserting an entry in the middle of a list shifts every following index and
Terraform destroys then recreates resources that had no reason to move.

## Capability targeted

Evolve a set of already applied resources by re-addressing them from index to
key, declaratively, and prove no existing resource is destroyed or replaced along
the way.

## Where the learner starts

`challenge/work` holds a configuration **already initialised and already
applied** (state present, produced files too), limited to the `random` and
`local` providers. Nothing in it is holed with `???`: it is correct but fragile
code.

- `variables.tf` declares `services`, a **list** of three strings, in this order:
  `web`, `cache`, `db`. `outputs.tf` exposes them as a positional list.
- `main.tf` creates, with `count`, one `random_pet` per service (its generated
  name is the instance's observable identity) and a `local_file` writing its
  record into `out/`.
- `DEMANDE.md` states the need: add the `api` service, to be placed between `web`
  and `cache`.

## The state to reach

1. No `count` any more: both resources are driven by `for_each` over a collection
   whose keys are the service names, literal strings known at plan time as
   Terraform requires.
2. The three existing instances are re-addressed from `[0]`, `[1]`, `[2]` to
   `["web"]`, `["cache"]`, `["db"]` **through `moved` blocks written in the
   configuration**, not through manual state manipulation.
3. The `random_pet` names of `web`, `cache` and `db` are **identical** to those
   before the migration: none of the three was recreated.
4. The `api` service is added: a single new instance per resource type, and
   nothing else moves.
5. The root output is a **map** indexed by key, built with a `for` expression:
   the `[*]` splat is invalid on a `for_each` resource.
6. The configuration is stabilised: an extra plan proposes nothing.

## How it is proven

The tests never read the `.tf` files, they drive Terraform and assert on the JSON.

- `terraform show -json`: every instance in `values.root_module.resources`
  carries a string `index` (`web`, `cache`, `db`, `api`), never an integer.
- **Central proof**: the addition's plan, saved by `plan -out` then read back by
  `show -json`, contains in `resource_changes` **exactly one `create` action per
  resource type, zero `delete`, zero `["delete","create"]`**.
- **No recreation**: the preserved `random_pet` names are compared to those
  captured before the migration (a fixture placed during preparation).
- **Declarative re-addressing**: in the re-addressing's JSON plan, the changes
  concerned carry a `previous_address` towards the old indexed address.
- `terraform output -json` returns an object whose keys are exactly the four
  service names, not an array.
- **Idempotence**: `terraform plan -detailed-exitcode` exits 0, not 2.
