# 🎯 Challenge: take over without regenerating the secret

## ✅ Objective

In `challenge/work`, the password in `mot-de-passe-existant.txt` is **already in
service**. Complete `main.tf` to **attach** it to `random_password.db` without
regenerating it, then write `app.conf` with that value.

A bare `terraform apply` is **forbidden**: it would draw a new password.

To do in `main.tf`:

1. **add an `import` block**: `to = random_password.db`, `id =
   file("${path.module}/mot-de-passe-existant.txt")`;
2. fill the **`length`** of `random_password.db` (the exact length of the existing
   password);
3. fill the **`content`** of `local_file.configuration`, of the form
   `"mdp=${random_password.db.result}"`.

Then apply: the `import` block attaches the existing object, with no regeneration.

## 🔍 Validation

`dsoxlab check state-understand-state` proves, on JSON and real state:

- `random_password.db.result` is **exactly** the fixture password (not a random
  value); `app.conf` contains it;
- the secret is **in clear text** in `state pull`, while marked in
  `sensitive_attributes`;
- a drift of `service.log` is seen by `plan` (exit 2) but not by
  `plan -refresh=false` (exit 0);
- `state push` refuses an older `serial` and a different `lineage`;
- idempotence, exactly 3 managed resources.

Stuck? `dsoxlab hint state-understand-state`.
