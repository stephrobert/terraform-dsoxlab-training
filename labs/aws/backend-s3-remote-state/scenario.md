# Scenario: a remote state, locked, and read by another stack

**Exam sub-objective covered: 3b (remote state), supported by 3d (sharing data
between configurations).**

Two beliefs trip candidates up on this objective: that declaring a `backend "s3"`
is enough to lock the state (locking is an opt-in, `use_lockfile` defaults to
`false`), and that a `backend` block takes variables like the rest of HCL. This
lab makes both fail, then repairs them.

## Target capability

Have a configuration write its state to an S3 bucket, with a genuinely active
lock, supplying the access parameters through partial configuration rather than
the named values a `backend` block forbids; then have a second configuration
consume that state's outputs without copying a single value.

## Where the learner starts

An S3 emulator runs locally on `http://localhost:14566`, declared under
`runtime.services`: `dsoxlab run` and `dsoxlab check` start it themselves.
`challenge/work` holds three directories:

- `bootstrap/`: complete, apply as is. It creates the state bucket, enables
  versioning and blocks public access. Its own state stays local, by necessity:
  the backend must exist before it can be used.
- `producer/`: a `random_pet` and three outputs already written. The
  `terraform {}` block is trapped: its `backend "s3"` declares
  `bucket = var.backend_bucket` and carries no locking argument. As it stands,
  `terraform init` stops on `Error: Variables not allowed`.
- `consumer/`: a `data "terraform_remote_state"` block whose `backend`, `config`
  and `defaults` are stubbed, plus four outputs that already reference
  `data.terraform_remote_state.producer.outputs.<name>`.

A `producer/floci.s3.tfbackend` file is provided half filled: `region`,
`use_path_style` and the `skip_*` are there; bucket, key, the locking argument
and the `endpoints` block are stubbed.

## The state to reach

1. The state bucket exists, versioning enabled, public access blocked.
2. The producer's `backend "s3"` block no longer references any named value.
3. The producer has no local `terraform.tfstate` left, and the state object
   exists in the bucket under the expected key.
4. The backend configuration Terraform actually retained carries `type: s3`, an
   `endpoints.s3` pointing at the emulator, `use_path_style` true and
   `use_lockfile` true.
5. Locking is effective: a `.tflock` object dropped by hand in the bucket makes a
   producer operation fail, and removing it lets it through again.
6. The consumer's state holds exactly one `mode: data` entry, of type
   `terraform_remote_state`, served by the built-in provider, and no managed
   resource.
7. The consumer's outputs match those published by the producer. A value changed
   upstream and reapplied propagates downstream without touching the consumer.
8. The consumer declares a `defaults` for an output the producer does **not**
   publish: the fallback is then returned.
9. Both configurations are idempotent.

## How it is proven

No test opens a learner `.tf` file, none reads human-facing Terraform output.

- The remote state: the S3 API lists the producer's key, and the producer
  directory must hold no `terraform.tfstate`. Both together, never one alone.
- The effective backend configuration: `.terraform/terraform.tfstate` is JSON
  written by Terraform, not learner code. The tests read `backend.type`,
  `backend.config.endpoints.s3`, `use_path_style` and `use_lockfile` there.
- The lock, by exit-code difference: the tests drop a valid `.tflock` themselves,
  run `terraform plan -lock-timeout=0s` and require a non-zero exit, then remove
  the object and require 0. Without `use_lockfile`, the same object is ignored
  and the plan passes: the test therefore fails precisely on the configuration
  the brief forbids.
- Data sharing: `terraform show -json` on the consumer must show a single
  `mode: data` entry of type `terraform_remote_state`, served by
  `terraform.io/builtin/terraform`, and no managed object.
- Propagation: the tests replay the producer with a different seed, replay the
  consumer, and check the outputs followed. A hard-coded value stays put and
  fails.
- Idempotence: `terraform plan -detailed-exitcode` must return 0 on both sides.

**Two corrections made to this scenario during construction.**

Point 8 originally claimed that a `defaults` pointed at a **non-existent** state
key would return the fallback instead of failing. Measured, that is false:
Terraform returns `Error: Unable to find remote state` in exit code 1. `defaults`
fills an **incomplete interface**, never an **absent** state. The check was
rebuilt on the case `defaults` actually covers: an output the upstream does not
publish.

**A constraint specific to this lab.** The producer's state is remote, so it is
shared by every copy of the working directory. A fault injected in one copy
changes the state all the others read. Counter-tests must therefore save the
state object beforehand and restore it between runs, and the reference solution
must be captured while the bucket holds the matching state.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/backend-s3-remote-state/
