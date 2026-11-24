# Pro · Objective 3, collaborative workflows

## The situation

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

## 🎯 Challenge: make two stacks collaborate without copying anything

### 📦 Starting point

`challenge/work` holds two independent stacks and a `CIBLE.md`.

| Directory | What it must do |
| --- | --- |
| `reseau/` | **publish** a platform: id, range, gateway |
| `application/` | **consume** those values, without ever copying them |

Each stack has its `backend.tfbackend` **supplied and complete**, and a `main.tf`
whose `terraform {}` block is a `???`.

Floci provides the S3 backend, and the `capstone3-etats` bucket already exists.

### ✅ Objective

1. **Pin the versions**: `required_version` on the binary, and a constraint on
   each provider.
2. **Send both states to the bucket**, under two distinct keys. No local
   `terraform.tfstate` left.
3. **Publish `reseau/`'s contract**: three outputs, the gateway among them,
   **computed** from the range and never hard-coded.
4. **Read the remote state** from `application/`, and derive a
   `raccordement.json` from it.
5. **Run everything in automation**: `-input=false`, `plan -out` then `apply` of
   the **plan file**.

### 🧭 Three things that decide the rest

**A `backend` block accepts no named value.** Neither variable nor local:
`Error: Variables not allowed`. The backend is resolved before any expression is
evaluated. Hence the empty block and the `-backend-config=backend.tfbackend`.

**What the upstream does not expose as an `output` is invisible from the other
side**, even if the value is in its state. Outputs are the stack's contract.

**A direct `apply` re-reads the configuration** when applying. Applying a saved
plan guarantees that what was reviewed is what goes out.

### ⚠️ Copying would pass today and fail tomorrow

One test replays `reseau/` with a different range and requires the downstream to
follow. Three hand-copied values stay frozen and fall.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone3-collaborative-workflows
```

Seven tests, none reading your `.tf`. The backend is proven by the absence of
local state **and** the presence of both keys in the bucket, queried on the Floci
side.

Stuck? `dsoxlab hint certifications-professional-capstone3-collaborative-workflows`.
