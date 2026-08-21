# Understand the Terraform state: what it knows, what it does not hide

The **state** is the link between your code and the real world: it maps each
address (`random_password.db`) to its corresponding real object. But it does
more, and that is where the traps are. It **keeps secrets in clear text**, it
**protects itself** against being overwritten by an older state, and it only
detects **drift** if it **refreshed** just before. This tutorial shows these three
facts; the challenge makes you prove them.

## Take over without recreating: the `import` block

When an object **already exists** (created by hand, or inherited), applying it as
is **recreates** it, which can be destructive. The **`import`** block (Terraform
1.5+) **attaches** it to the state, without recreating it, and applies with
`terraform apply`:

```hcl
import {
  to = random_password.db
  id = "the-existing-value"
}
resource "random_password" "db" {
  length = 20
}
```

After apply, `random_password.db.result` carries the **existing** value, not a new
one. That is the difference between taking over and breaking everything.

## The secret is in clear text in the state

A common belief is that `sensitive` **protects** a secret. It does not: it only
hides the **display**. In the state, the value is **in clear text**:

```bash
terraform state pull | jq '.resources[] | select(.type=="random_password")
  | .instances[0].attributes.result'
```

The same instance carries `result` in its **`sensitive_attributes`** array: the
mark exists, but it hides **nothing** of the state file's content. That is why a
state is encrypted at rest and stored in a protected backend.

## Drift is only seen with a refresh

Terraform does not "watch" your infrastructure. It only sees **drift** (a change
made outside Terraform) when it **refreshes** the state by re-reading the real
world, which a `plan` does by default:

- `terraform plan` (with refresh) on an object changed outside Terraform returns
  **`2`** (`-detailed-exitcode`): the drift is seen.
- `terraform plan -refresh=false` returns **`0`**: without re-reading reality, the
  state alone sees nothing.

That pair of codes proves the detection comes from the **refresh**. A CI that runs
with `-refresh=false` for speed can therefore **miss** drift.

## The state protects itself: serial and lineage

Two state fields guard its integrity:

- **`serial`** increments on every write. `terraform state push` **refuses** a
  state with a **lower** `serial` (`cannot import state with serial ... over newer
  state ...`): you do not accidentally put back a stale state.
- **`lineage`** identifies the state's lineage. Pushing a state with a
  **different** `lineage` is also refused, but with a **distinct** message
  (`unrelated state with lineage ...`).

These guards exist to prevent a destructive overwrite. You force them with
`-force`, at your own risk.

## Your turn

You know that an `import` block takes over without recreating, that the secret is
in clear text in the state despite `sensitive`, that drift only appears with a
refresh, and that `state push` refuses an older `serial` or a different `lineage`.
The challenge makes you attach a password already in service, without regenerating
it, and proves it.

```bash
dsoxlab run state-understand-state
dsoxlab check state-understand-state
dsoxlab hint state-understand-state
```

Target exam objective: **1e**, Professional level.

Reference: [Understand the state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/comprendre-state/)
