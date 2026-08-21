# Scenario: when sensitivity breaks for_each

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

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/sensitive-terraform/
