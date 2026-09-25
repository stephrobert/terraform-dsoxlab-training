# 🎯 Challenge: one word, two meanings, two attachment strategies

## 📦 Starting point

`challenge/work` holds three directories. **No account, no `terraform login`**:
this lab creates nothing in HCP Terraform.

| Directory | State |
| --- | --- |
| `nomme/` | **three faults**, must attach by name to `app-prod` |
| `etiquete/` | **two faults**, must attach by tags |
| `questionnaire/questionnaire.tf` | **supplied**, do not change |
| `questionnaire/reponses.auto.tfvars` | five `???` to answer |

## ✅ Objective

1. **Repair `nomme/`** so it attaches to the `app-prod` workspace of the
   `atelier-dsoxlab` organization, **by name**.
2. **Repair `etiquete/`** so it attaches **by tags**, with a `project` and no
   `name`.
3. **Answer the five questions**, with the words the enumeration allows.

## 🧭 Run `validate`, then `init`, and compare

That comparison is the lab's whole point. `terraform validate` answers
"Success! The configuration is valid." on two of the three faults in `nomme/`.
Only `init` sees them, because a `cloud` block is resolved when Terraform works
out where the state lives, before any expression is evaluated.

One consequence follows, and it is one of the five questions.

## ⚠️ Where you stop, and it is normal

A **correct** configuration ends up here:

```
Initializing HCP Terraform...

Error: Required token could not be found
```

That error is the goal, not a failure: it means your attachment was accepted and
Terraform is now asking to authenticate. A faulty configuration never gets that
far.

Careful though: two of the faults print that same line **next to** their own
error. Read everything `init` prints, not just the last line.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-hcp-workspaces
```

Eight tests. The two directories are initialized in an environment stripped of
every token, so the measurement is the same on any machine, including one that
has already run `terraform login`.

An answer outside the enumeration is refused **at plan time**, with a message
saying what to write.

Stuck? `dsoxlab hint hcp-terraform-hcp-workspaces`.
