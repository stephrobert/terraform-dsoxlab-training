# Scenario: Pro · Objective 3, collaborative workflows

**Exam objective targeted: 3** (3a version constraints on the binary, providers and
modules, 3b remote state, 3c workflow in automation, 3d sharing data across
configurations and workspaces).

## Capability targeted

Make **two separate configurations collaborate** through a shared remote state, pinning
versions and running **without human interaction**, as a CI would.

## Where the learner starts

Floci runs locally and provides the **S3** backend. Two independent stacks live in
`challenge/work`:

- `reseau/`: produces a base infrastructure and must **publish** its identifiers as
  outputs.
- `application/`: must **consume** those values without ever hard-coding them.

Both stacks have an incomplete `terraform {}` block: no backend, no `required_version`, no
constrained `required_providers`. Each has a complete `backend.tfbackend` supplied, since
configuring the S3 backend itself is already covered by another lab.

## The state to reach

1. Both stacks write their state to the **S3 backend on Floci**, each under a distinct
   key. No local `terraform.tfstate` left.
2. `application/` reads `reseau/`'s values through the `terraform_remote_state` data
   source. **No hard-coded value**: changing a value upstream must propagate.
3. Versions are pinned: `required_version` on the binary and a version constraint on the
   provider.
4. Everything runs in **automation mode**: `-input=false`, with a saved plan then applied
   (`plan -out` then `apply` of the plan file).

## How it is proven

- The S3 bucket on Floci holds both state keys, queried through the local endpoint with
  the credentials header: Floci accepts unsigned requests but isolates by credentials, so
  a request without it would see nothing and the test would wrongly conclude the bucket is
  empty.
- The downstream state holds a `mode: data` entry of type `terraform_remote_state`: values
  copied by hand would produce none.
- **The decisive test**: the upstream stack is replayed with a different network range, the
  downstream plan must then exit 2, and after applying, the downstream must carry the new
  value. A 0 there means the downstream reads nothing. Everything is restored afterwards,
  whatever happens.
- Both stacks pass `plan -out` then `apply` of the plan file with `-input=false`: the
  configuration is genuinely automatable.
- Idempotence on both stacks.
