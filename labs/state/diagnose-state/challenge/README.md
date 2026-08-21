# 🎯 Challenge: a drift to prove, an inherited token to adopt

## 📦 Starting point

`challenge/work` holds a project that was **never applied**. Building the
reference state is on you, and so is causing the incident: the drift in this lab
is **real**, not prefabricated.

```bash
terraform init
terraform apply
```

| File | What it is |
| --- | --- |
| `main.tf` | the configuration, complete, **do not modify** |
| `adoption.tf` | the adoption to come, **commented out** and holed with `???` |
| `token-herite.txt` | a token created outside Terraform, **impossible to regenerate** |

`adoption.tf` ships commented out for a precise reason: uncommented **before**
the first `apply`, it would **create** a random token instead of adopting the one
that already exists.

## ✅ Objective

Prove a drift, reconcile it, then adopt the inherited token **without Terraform
regenerating it**.

## 📋 What you must obtain

1. **Cause the incident**: after the first `apply`, overwrite `data/note.txt` by
   hand, the way a colleague in a hurry would.
2. A **`derive-plan.json`** file proving the drift: it carries a `resource_drift`
   entry for `local_file.note`, and its `resource_changes` is **empty**. Since a
   plan file is binary, it takes two steps,
   `terraform plan -refresh-only -out=...` then
   `terraform show -json ... > ...`.
3. `terraform plan -refresh-only -detailed-exitcode` exits **0**: the state
   describes what actually exists again.
4. `data/note.txt` is back to the content declared in `main.tf`.
5. `random_string.legacy` is in the state, its `result` attribute holding
   **exactly** the string from `token-herite.txt`.
6. `terraform plan -detailed-exitcode` exits **0**. Both codes are therefore
   **0 at the same time**.

## ⚠️ The heart of the matter

Two traps, independent of each other.

**The first is about diagnosis.** An ordinary plan stores the drift **both** in
`resource_drift` and in `resource_changes`; only `plan -refresh-only` leaves
`resource_changes` empty. That absence is what the test requires, and it proves
you used the right tool.

**The second is about adoption.** Team policy mandates `length = 24` for every
new token, and the inherited one is shorter. Without a guard rail, Terraform does
not merely adopt:

```text
  # random_string.legacy must be replaced
  # (imported from "...")
  # Warning: this will destroy the imported resource
```

Applied without reading, that plan **regenerates** the token, and the next plan
calmly reports `No changes`. The loss is then invisible. **Read the plan before
applying.**

## 🔍 Validation

`dsoxlab check state-diagnose-state` proves, by execution:

- `derive-plan.json` really is a **refresh-only** plan document carrying the
  drift of `local_file.note`;
- both `-detailed-exitcode` return **0**, which reads as two distinct
  statements: the state matches the real world, and the real world matches the
  code;
- `data/note.txt` holds the content the state attributes to it;
- the token in the state is **identical** to the one in `token-herite.txt`: a
  regenerated value cannot match by chance;
- the state carries exactly the two expected addresses.

No test opens your `.tf` files.

Stuck? `dsoxlab hint state-diagnose-state`.
