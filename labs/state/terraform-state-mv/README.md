# Renaming without destroying: `terraform state mv` and the `moved` block

Renaming a block, or pushing it into a module, changes its **address**. And the
address is an object's identity in the state: by default Terraform reads that
change as "the old object is gone, a new one appeared", so as a **destroy
followed by a create**. Two mechanisms avoid that, and they are not equivalent.
This tutorial shows both; the challenge will have you use each in its place.

## The problem, in one command

Take an applied project whose resource is renamed in the code without touching
the state:

```bash
terraform plan
```

```text
Plan: 3 to add, 0 to change, 3 to destroy.
```

Three creations and three destructions, although nothing changed in the
infrastructure. Terraform does not guess a rename: it compares addresses, and
finds none of them. On a generated password or a database, that reading is
expensive.

## `terraform state mv`: reconciling a state that lags behind

The command moves a state entry from one address to another. It **never** touches
the real infrastructure: it only changes the link between the state and the
remote object.

```bash
terraform state mv random_pet.web random_pet.frontend
```

```text
Move "random_pet.web" to "random_pet.frontend"
Successfully moved 1 object(s).
```

Two constraints are not up for invention:

- both addresses must refer to the **same kind of object** (an instance to an
  instance, a whole module to a whole module);
- for a resource, the **type must be identical**: you rename `random_pet.web`
  into `random_pet.frontend`, never into `random_string.frontend`.

The `-dry-run` option shows what would move without writing anything. The command
also accepts `-lock`, `-lock-timeout` and, for the local backend only, the legacy
`-state`, `-backup` and `-backup-out` options.

**Order matters, and that is the part people skip.** Change the code **first**,
run the command **after**. In between, anyone running a `plan` or an `apply`
against the same state sees one object to destroy and another to create, and may
apply that reading. The documentation makes it its only warning: you must ensure
nobody makes another change in that window. On a shared backend, a **single** run
is enough for the whole team, since it acts on the state, not on your machine.

## The `moved` block: refactoring from the code

Since Terraform **1.1**, the move is declared in the code. Two references, no
quotes:

```hcl
moved {
  from = random_string.db_secret
  to   = module.secret.random_string.this
}
```

At the next plan, Terraform announces a move instead of a replacement:

```text
  # random_string.db_secret has moved to module.secret.random_string.this
Plan: 0 to add, 0 to change, 0 to destroy.
```

The `apply` finalises it without destroying or creating anything. The machine
proof is in the plan JSON, and it is what tells the two methods apart:

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.resource_changes[]
  | select(.previous_address) | {address, previous_address, actions: .change.actions}'
```

```json
{
  "address": "module.secret.random_string.this",
  "previous_address": "random_string.db_secret",
  "actions": ["no-op"]
}
```

**Terraform only writes `previous_address` when a `moved` block was taken into
account.** `terraform state mv` never produces it: the state is already moved by
the time the plan is computed, so there is nothing left to report.

## Do not delete an applied `moved` block

This is the costliest trap, and it is counter-intuitive: once the move is
applied, you are tempted to drop the now-useless block. Drop it, and any
configuration still referring to the old address **plans a deletion** instead of
a move.

Checkable in a minute: bring the object back to its old address, remove the
block, plan again. The `no-op` becomes a `delete` plus a `create`.

The documentation is explicit: removing a `moved` block is a **breaking change**,
and it recommends **retaining all historical** blocks to preserve the upgrade
path. The only tolerance concerns a **private** module whose users you are
certain have all applied.

## Which one, and when

| Situation | Method |
| --- | --- |
| The code is already refactored, the state lags behind | `terraform state mv` |
| The refactoring starts from the code, under review | `moved` block |
| A shared module, consumed by others | `moved` block, retained |
| Terraform older than 1.1 | `terraform state mv`, the only option |

The official documentation inverts the hierarchy people assume: the `moved` block
is the **normal** mode of refactoring, and `state mv` the way out for versions too
old. The reason is simple: an imperative command leaves **no trace** in the
repository, whereas a versioned block is read, reviewed and replayed identically
by the whole team.

## Your turn

You know an unreconciled rename amounts to a destruction, that `state mv` repairs
a lagging state without touching reality, that the `moved` block declares the move
in the code, that `previous_address` proves which of the two was used, and that an
applied block is not deleted. The challenge hands you a project whose code was
refactored without anyone touching the state: three objects to reattach, two
methods to use where each belongs.

```bash
dsoxlab run state-terraform-state-mv
dsoxlab check state-terraform-state-mv
dsoxlab hint state-terraform-state-mv
```

Target exam objective: **1e** (inspect and manipulate state), Associate level.

Reference: [terraform state mv](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-mv/)
