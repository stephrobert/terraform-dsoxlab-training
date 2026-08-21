# Scenario: the state knows everything, including what it should not

**Target exam objective: 1e.**

The state is not a simple lookup table: it keeps secrets in clear text, it refuses to be overwritten by an older state, and it only reports drift if Terraform re-read the real world just before. The trap here is the plan that announces "no changes" while the infrastructure has moved.

## Target capability

Take over an object that already exists **without recreating it** (an `import` block), observe that the secret it carries ends up **in clear text** in the state, tell a plan that refreshed from a plan that did not, and know that an older state cannot be put back with `state push`.

## Where the learner starts

`challenge/work` contains neither `terraform.tfstate` nor `.terraform`. `local` and `random` providers only, no VM, no cloud.

- `versions.tf`, `variables.tf`: complete, do not touch.
- `mot-de-passe-existant.txt`: a fixture. Twenty characters, no trailing newline. This is the password **already in service** in the application, the one it is **forbidden to regenerate**.
- `main.tf`: three resources, some `???`. `random_password.db` has a holed `length`. `local_file.configuration` writes `app.conf` in `0600` with a holed `content`. `local_file.journal` writes `service.log` and is self-sufficient. The **`import` block** must be added.

The obvious shortcut is forbidden: a bare `terraform apply` would draw a new password, `app.conf` would carry a value unknown to the application, and the lab would be lost **with no error message**. You must first **attach** the existing password.

## The target state

1. The state contains exactly **three** resources in `mode: managed`, none in `mode: data`.
2. `random_password.db.result` is **exactly** the string in `mot-de-passe-existant.txt`: the value was not drawn at random, it was **attached** by an `import` block applied on the first `apply`.
3. `app.conf` contains that same string (`content` of `local_file.configuration`).
4. A `terraform plan` right after apply proposes nothing.

## How it is proven

The tests drive Terraform and never read the learner's `.tf` files. The `mot-de-passe-existant.txt` fixture is read: it is the expected reference.

1. **Takeover without regeneration**: `show -json`, `random_password.db.result` equal, character for character, to the fixture content (comparison after JSON decoding, never on raw text). A learner who simply applied gets another string and fails. `app.conf` contains the same value.
2. **Secret in clear text**: `terraform state pull`, the `random_password.db` instance has `attributes.result` in clear text **and** `result` in `sensitive_attributes`. The mark exists, the protection does not.
3. **Drift and refresh**: the test writes a line into `service.log` outside Terraform, then requires `plan -detailed-exitcode` = `2` and `plan -refresh=false -detailed-exitcode` = `0` on that drift. An `apply` restores, then `plan` falls back to `0`. That pair of codes proves the detection comes from the **refresh**, not the state.
4. **State guard**: the test builds a copy of the current state with a lower `serial`, pushes it with `terraform state push`, and requires a refusal (`cannot import state with serial ... over newer state ...`) plus an unchanged current `serial`. It replays on a copy with a different `lineage`: the refusal is also expected, but the message **differs** (`unrelated state with lineage ...`).
5. **Idempotence**: `plan -detailed-exitcode` = `0`, and no managed resource beyond the three expected.

None of these checks passes on an empty `challenge/work`, nor on a directory where the learner just did an `init` followed by an `apply`.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/comprendre-state/
