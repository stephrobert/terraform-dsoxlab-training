# Prove what the state lock actually blocks

## The situation

**Target exam objective: 3b, manage remote state, its locking and its recovery after an incident.**

Four things are commonly believed about state locking, and all four are wrong:
that only `apply` is concerned, that locking is on by default on every backend
that supports it, that the lock file always lives at the project root, and that
a lock file left on disk after a crash blocks everything that follows. This lab
puts them to the test instead of repeating them.

## Target capability

Establish experimentally the exact scope of locking on a local backend (what it
rejects, what it lets through, where it is written, how it is released), then
state the configuration that enables it on an S3 backend. The point is not to
type `terraform force-unlock`, it is to know whether the lock in front of you is
alive or is only a leftover file: the wrong answer deletes a lock while a
colleague is applying.

## Where the learner starts

`challenge/work` holds two incomplete files. In `main.tf`, the `path` of the
`backend "local"` block is punched out with `???`, and so is the command of the
`local-exec` provisioner of a `terraform_data` resource. In `observations.tf`,
four outputs are waiting for the learner's findings. No `.terraform/`, no state.
A `shell` lab with no external provider: `terraform_data` is built into
Terraform, so the lab runs offline, with no VM and no cloud account. Making the
apply slow enough for a lock to be observable conditions everything else.

## Target state

1. The local backend points at a state outside the root, `etat/projet.tfstate`,
   the directory is initialised, the configuration applied and converged, and
   its apply lasts at least fifteen seconds.
2. The `fichier_verrou` output gives the real path of the lock file, relative to
   the project root.
3. The `codes_pendant_verrou` output gives the exit code observed for six
   actions attempted while a lock is held: `plan`, `apply`, `plan -lock=false`,
   `force-unlock`, `state list` and `show -json`.
4. The `verrou_residuel` output gives the exit code of a `plan` run again while
   a lock file is still lying around after an abrupt stop, and states whether
   that file is still there after that `plan`.
5. The `backend_s3` output names the argument that enables native S3 locking,
   says whether it is active with no configuration at all, and gives the status
   of DynamoDB table based locking.
6. Once the apply is over, no lock file remains.

## How it is proven

The tests run in `challenge/work`, never open the learner's `.tf` files and read
no human-facing output.

- The backend is read from `.terraform/terraform.tfstate`, the machine artefact
  produced by `init`: `backend.type` is `local` and `backend.config.path` the
  expected path. `terraform show -json` describes the slow resource as
  `mode: managed` and `terraform plan -detailed-exitcode` returns 0.
- The tests redo the experiment: they launch an apply in the background, wait
  for the lock to appear, take their own readings of the exit codes for points 3
  and 4, kill an apply with `kill -9` to manufacture a leftover file, then
  compare their own measurements with the declared outputs. Nothing is hardcoded
  on the expected-result side.
- The captured lock is checked against its documented shape: exactly seven keys,
  `Operation` equal to `OperationTypeApply`, `ID` in UUID format, `Version`
  equal to the `terraform_version` of `terraform version -json`, and `Path`
  equal to the configured state path, not to the lock file path.
- Four received ideas fall: the concurrent `plan` errors out, the local
  `force-unlock` fails whatever happens, the `plan` run after an abrupt stop
  succeeds despite the leftover file, and that file is removed by Terraform
  itself.
- Only `backend_s3` is not measurable offline: it is compared with the official
  S3 backend documentation, `use_lockfile`, `false` by default, DynamoDB table
  based locking deprecated.
- None of these proofs passes on an empty directory, nor on a directory whose
  apply would be too fast for a lock to be observable.

## 🎯 Challenge: measure what the lock blocks, and what it lets through

### ✅ Objective

In `challenge/work`, two files carry `???` markers. To do:

1. **`main.tf`**: set the `path` of the `backend "local"` block to
   **`etat/projet.tfstate`** (the state must leave the root), and give the
   provisioner a command that holds the apply for **at least fifteen seconds**;
2. **`observations.tf`**: take the measurements, then fill the four outputs with
   what you actually **observed**.

Measurements are taken from a second terminal while a `terraform apply` runs in
the first one. Record **exit codes** (`echo $?`), not messages:

```bash
terraform plan -input=false > /dev/null 2>&1; echo $?
```

For `verrou_residuel`, kill the running apply (`kill -9`), check whether the lock
file is still there, run a `plan` again, note its exit code, then look for the
file once more.

For `backend_s3`, the answer is in the official S3 backend page: the name of the
locking argument, its default value, and the status of DynamoDB table based
locking.

### 🔍 Validation

`dsoxlab check state-state-locking` **redoes the experiment** and compares its
own measurements with yours:

- `.terraform/terraform.tfstate` carries `backend.type = local` and
  `backend.config.path = etat/projet.tfstate`;
- the replacement apply does last at least fifteen seconds, otherwise no lock is
  observable and nothing can be measured;
- the captured lock carries **seven** fields, a UUID `ID`, your CLI `Version`,
  and a `Path` that designates the state;
- your four outputs are checked against the test's own readings, action by
  action;
- no lock file remains at the end, and `plan -detailed-exitcode` returns 0.

Stuck? `dsoxlab hint state-state-locking`.
