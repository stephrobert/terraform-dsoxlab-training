# 🎯 Challenge: fix the typo, let JSON win

## Starting point

`challenge/work` holds an **applicable** project: `versions.tf`, `variables.tf`
(`region`, `bucket` default `app-defaut`, `replicas` default 1), `main.tf`
(provided), and a **degraded** `terraform.tfvars`:

```hcl
region   = "eu-west-3"
bukcet   = "prod"     # typo
replicas = 2
```

`terraform apply` **succeeds** (the undeclared variable is only a warning), but
`bucket` stays at `app-defaut`.

## ✅ Objective

1. **Fix the typo** in `terraform.tfvars`: `bukcet` → `bucket`, so `bucket` is
   `prod`. An undeclared variable in a `.tfvars` is only a **warning**: it breaks
   nothing, it leaves the real variable at its default.
2. **Create a `terraform.tfvars.json`** setting `replicas = 5`. Since the **JSON
   variant outranks** `terraform.tfvars` (which sets 2), `replicas` must be **5**.

After `apply`, a second `terraform plan` must propose nothing.

## 🧭 What the lab makes you observe

- **A typo in a `.tfvars` does not break the plan**: it produces a warning and
  the variable stays at its default.
- **`terraform.tfvars.json` beats `terraform.tfvars`**: a distinct, stronger
  precedence level.

## 🔍 Validation

```bash
dsoxlab check write-code-tfvars-files
```

Four tests reading `terraform output -json`: `bucket` at `prod` (typo fixed),
`replicas` at 5 (JSON wins), `region`, and idempotence. None reads your `.tf`.
