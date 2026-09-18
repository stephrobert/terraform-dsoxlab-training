# 🎯 Challenge: prove that Terraform has a memory

## Starting point

`challenge/work` contains four files:

- `versions.tf`: **complete, do not modify**. It pins `random`, `local` and
  `null`. The third is used by no resource, and must still end up in the lock
  file.
- `main.tf`: **full of holes**. The `random_pet` length, then the `content` and
  the `filename` of the `local_file`, are `???`. A `local_file` data source is
  to be completed as well.
- `outputs.tf`: **full of holes**. Three outputs, one of which must be declared
  sensitive.
- `inventaire.txt`: a hand-written file **nobody declared**.

Nothing is initialised: no `.terraform/`, no lock, no state.

## ✅ Objective

Replace every `???`, then apply.

1. **`random_pet.nom`**: two words, separated by a dash.
2. **`local_file.rapport`**: its content must be **built** from the identifier
   produced by `random_pet`, never pasted by hand. The file is written in the
   module directory.
3. **`data.local_file.inventaire`**: read `inventaire.txt` **without managing
   it**.
4. **The three outputs**: the generated name, the report path, and a third one
   derived from the name with `upper()`, declared **`sensitive`**.

After `apply`, a second `terraform plan` must propose nothing.

## 🧭 What the lab makes you observe

- **`null` appears in the lock** although no resource uses it:
  `required_providers` is enough to have it installed and locked.
- **The state holds three entries, but only two managed resources.** The third
  is in `data` mode: Terraform will neither create nor destroy it.
- **`inventaire.txt` stays invisible.** It exists on disk, no resource claims
  it, and Terraform never cares about it once.
- **Delete the report, then plan**: a single create is announced, and the
  `random_pet` stays `no-op`. Its identity survived the drift.
- **The sensitive output is hidden on screen and in the clear in
  `terraform.tfstate`.** The flag describes a display, not a protection.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-overview
```

Eight tests reading `terraform show -json`, `output -json`, the lock file and
exit codes: the locked providers, the two managed resources, the distinct data
source, the identifier actually produced by Terraform, the `sensitive` mask
against the clear text of the state, idempotence through `-detailed-exitcode`,
drift tested on a **copy** of your work, and finally the consistency of the state
with the disk. None of them reads your `.tf`.
