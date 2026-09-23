# 🎯 Challenge: what Terraform manages, what it merely reads

## Starting point

`challenge/work` holds four files:

- `catalogue.txt`: **it already exists**. Nobody created it with Terraform, and
  Terraform must never destroy it.
- `versions.tf`: **full of holes**. The `required_providers` block is empty.
- `main.tf`: **full of holes**. The keyword of the first block, the summary
  content, and the two triggers.
- `outputs.tf`: **full of holes**. Two outputs.

There is no `.terraform/`, no state, no lock file.

## ✅ Objective

1. **Declare the three providers** `local`, `null` and `random` with their
   `source` and a **pessimistic** constraint (`~> x.y`).
2. **Pick the right nature** for the block targeting `catalogue.txt`. It must
   read it, not own it.
3. **Derive** the content of `resume.txt` from what that block read, and from
   the reference produced by `random_pet`.
4. **Feed the trigger** of `null_resource` with both natures at once.
5. **Expose two outputs**: the produced reference, and the number of lines in
   the catalogue.

## 🧭 What the lab makes you observe

- **The state tells both natures apart without ambiguity.** `"mode": "managed"`
  on one side, `"mode": "data"` on the other, with an address prefixed by
  `data.`.
- **The reference alone creates the dependency.** `data.TYPE.NAME.ATTRIBUTE` on
  one side, `TYPE.NAME.ATTRIBUTE` on the other: a hand-written `depends_on` is
  almost always the symptom of a missing reference.
- **Change `catalogue.txt` without touching a single `.tf`, and the plan
  moves.** A data source is re-read on every plan. If the plan stays empty, the
  value being read irrigates nothing.
- **After `destroy`, `resume.txt` is gone and `catalogue.txt` is intact.** That
  is the full demonstration: write `resource` instead of `data`, and Terraform
  erases a file it never created.

## 🔍 Validation

```bash
dsoxlab check getting-started-providers-resources-data-sources
```

Eight tests reading `terraform show -json`, `output -json`, the lock file and
exit codes. The two destructive tests, the one changing the catalogue and the
one destroying, work on a **copy** of your work: a test does not break what it
measures. None of them reads your `.tf`.
