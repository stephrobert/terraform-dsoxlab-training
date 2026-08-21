# 🎯 Challenge: a remote state, locked, and read

## 📦 Starting point

The S3 emulator already runs on `http://localhost:14566`: `dsoxlab` starts it for
you. No AWS account is needed.

| Directory | What it is |
| --- | --- |
| `bootstrap/` | **complete**, apply as is. Its state stays **local**, by necessity |
| `producer/` | three outputs written, and a `terraform {}` block **trapped twice** |
| `consumer/` | a **stubbed** `data` block, and four outputs already written |
| `producer/floci.s3.tfbackend` | provided **half filled** |
| `CIBLE.md` | the state to reach, and the order of operations |

## ✅ What you must achieve

1. The bucket exists, versioning on, public access blocked.
2. The `backend "s3"` block references **no** named value any more.
3. The producer has **no** local state left, and the object is in the bucket.
4. The retained configuration carries `use_path_style` **and** `use_lockfile`
   set to true, plus an `endpoints.s3` pointing at the emulator.
5. The lock is **effective**: a dropped `.tflock` makes an operation fail.
6. The consumer holds **one** `mode: data` entry and **no** managed resource.
7. Its outputs match the producer's, and **follow** when upstream changes.
8. The `defaults` returns the fallback for the output the producer does not
   publish.
9. Both configurations are **idempotent**.

## ⚠️ The two traps in the `terraform {}` block

**It references a variable.** Run `terraform init` and read the answer: it
explains why partial configuration exists.

**It requests no locking.** The S3 backend lock is an **opt-in**: `use_lockfile`
defaults to `false`. Without it, a lock file dropped in the bucket is simply
**ignored**.

## 🔍 Validation

`dsoxlab check aws-backend-s3-remote-state` proves, by execution:

- the bucket and its **versioning**, queried through the S3 API;
- the backend configuration **actually retained**, read from
  `.terraform/terraform.tfstate`;
- that the state object is in the **bucket** and that **none** is left locally,
  both together;
- the **lock**, by exit-code difference: the validation drops a `.tflock` itself,
  requires the plan to **fail**, then removes it and requires it to **pass**;
- that the consumer really reads the **remote state**, served by the built-in
  provider;
- **propagation**: upstream is replayed with a different seed, and downstream
  must follow. A copied value stays frozen and fails.

Stuck? `dsoxlab hint aws-backend-s3-remote-state`.
