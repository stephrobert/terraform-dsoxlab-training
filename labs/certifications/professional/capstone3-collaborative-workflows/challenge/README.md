# 🎯 Challenge: make two stacks collaborate without copying anything

## 📦 Starting point

`challenge/work` holds two independent stacks and a `CIBLE.md`.

| Directory | What it must do |
| --- | --- |
| `reseau/` | **publish** a platform: id, range, gateway |
| `application/` | **consume** those values, without ever copying them |

Each stack has its `backend.tfbackend` **supplied and complete**, and a `main.tf`
whose `terraform {}` block is a `???`.

Floci provides the S3 backend, and the `capstone3-etats` bucket already exists.

## ✅ Objective

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

## 🧭 Three things that decide the rest

**A `backend` block accepts no named value.** Neither variable nor local:
`Error: Variables not allowed`. The backend is resolved before any expression is
evaluated. Hence the empty block and the `-backend-config=backend.tfbackend`.

**What the upstream does not expose as an `output` is invisible from the other
side**, even if the value is in its state. Outputs are the stack's contract.

**A direct `apply` re-reads the configuration** when applying. Applying a saved
plan guarantees that what was reviewed is what goes out.

## ⚠️ Copying would pass today and fail tomorrow

One test replays `reseau/` with a different range and requires the downstream to
follow. Three hand-copied values stay frozen and fall.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone3-collaborative-workflows
```

Seven tests, none reading your `.tf`. The backend is proven by the absence of
local state **and** the presence of both keys in the bucket, queried on the Floci
side.

Stuck? `dsoxlab hint certifications-professional-capstone3-collaborative-workflows`.
