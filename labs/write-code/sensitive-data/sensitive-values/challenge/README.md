# When sensitivity breaks for_each

## The situation

**Exam objective: 2f (managing sensitive data), Professional level.**

`sensitive` masks display, but it has a rarely taught side effect: a sensitive value cannot be a `for_each` key. Marking a variable `sensitive` can therefore break a working configuration. The learner must iterate over non-sensitive keys while injecting a secret, and expose a fingerprint without leaking.

## Target capability

Understand that sensitivity propagates and has side effects: a sensitive value forbidden as a `for_each` key (`Invalid for_each argument`), a contaminated attribute flagged in `sensitive_values`, and a secret `sha256` that stays sensitive until declassified with `nonsensitive()`.

## Where the learner starts

`challenge/work/` holds an incomplete project. No VM, no remote account: only `local` is used. The lab runs anywhere `terraform` is on the PATH, offline.

The directory has `versions.tf`, `variables.tf` (`services`, non-sensitive set; `db_password`, sensitive), a `main.tf` where `local_file.conf`'s `for_each` is holed, and a holed `outputs.tf`:

```hcl
resource "local_file" "conf" {
  for_each = ???        # iterate over the NON-sensitive services (not a sensitive value)
  filename = "${path.module}/out/${each.key}.conf"
  content  = "service=${each.key}\npassword=${var.db_password}\n"   # contaminates content
}
output "empreinte" { value = ??? }   # sha256 of the secret, declassified
```

`terraform apply` fails as-is: the `???` are not valid HCL, and a sensitive value as a `for_each` key would be rejected anyway.

## The state to reach

1. `local_file.conf` iterates over `var.services` (non-sensitive): two instances, keys `web` and `db`. A sensitive `for_each` key would raise `Invalid for_each argument`.
2. Each `conf`'s `content` attribute is flagged sensitive in the state's `sensitive_values`, because it injects `var.db_password`.
3. `empreinte` exposes the password's `sha256` **declassified** with `nonsensitive()`: the output is not sensitive, and it is a hash, not the secret.
4. The project converges: a second plan right after apply proposes nothing.

## How it is proven

The tests never open the learner's `.tf` files. They read `terraform show -json` (including `sensitive_values`), `output -json` and return codes.

1. `terraform show -json`: the `conf` instances have indices `web` and `db` (the `for_each` succeeded on non-sensitive keys).
2. Still in that JSON, each `conf` has `sensitive_values.content` at `true`: contamination is traced.
3. `terraform output -json`: `empreinte` is not sensitive and is 64 hex characters.
4. `terraform plan -detailed-exitcode` returns 0 right after apply.

Reference: https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/sensitive-terraform/ (in French)

## 🎯 Challenge: iterate without leaking

### Starting point

`challenge/work` holds `versions.tf`, `variables.tf` (`services`, a NON-sensitive
set; `db_password`, sensitive), `main.tf` (`local_file.conf`'s `for_each` is
holed), and `outputs.tf` (holed). `terraform apply` fails as-is.

### ✅ Objective

1. **`main.tf`, `for_each`**: iterate over **`var.services`** (non-sensitive). A
   **sensitive** value as a `for_each` key is rejected (`Invalid for_each
   argument`). The `content` injects `var.db_password` (do not modify) and
   contaminates the attribute.
2. **`outputs.tf`, `empreinte`**: expose the password's **`sha256`** **without**
   disclosing it or making the output sensitive. The `sha256` of a secret stays
   sensitive: **declassify** it with `nonsensitive()`.

After `apply`, a second `terraform plan` must propose nothing.

### 🧭 What the lab makes you observe

- **A sensitive value cannot be a `for_each` key**: marking `sensitive` can break
  a `for_each`.
- **Contamination is read in `sensitive_values`** (`content` at `true`).
- **`nonsensitive()`** publishes a hash without disarming the secret.

### 🔍 Validation

```bash
dsoxlab check write-code-sensitive-data-sensitive-values
```

Four tests reading `terraform show -json` and `output -json`: the non-sensitive
`for_each` keys, the `content` contamination, the declassified fingerprint, and
idempotence. None reads your `.tf`.
