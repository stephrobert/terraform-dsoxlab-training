# 🎯 Challenge: make a run execute at HashiCorp

## ⚠️ The only lab that needs an account

The other seven `hcp-terraform` labs need nothing. This one needs an HCP
Terraform account — the free plan is enough — and an API token on your machine:

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

Without a token the tests **skip**: you will not see red, you will see where to
find what is missing. The guide is [`docs/hcp-token.md`](../../../../docs/hcp-token.md).

## 📦 Starting point

| File | State |
| --- | --- |
| `plateforme/organisation.auto.tfvars` | one `???`: **your** organization |
| `plateforme/plateforme.tf` | four `???` |
| `plateforme/versions.tf`, `variables.tf` | **supplied** |
| `application/versions.tf` | the `cloud` block is missing |
| `application/main.tf` | **supplied**, do not change |

## ✅ Objective

1. **Supply your organization**, the one in the URL
   `app.terraform.io/app/<here>`.
2. **Complete `plateforme/`**: a workspace inside the project, execution
   settings, a sensitive variable. Then apply.
3. **Attach `application/`** to the created workspace and run the apply. That is
   where the run leaves for HCP Terraform.

```bash
cd plateforme && terraform init && terraform apply
cd ../application && terraform init && terraform apply
```

## 🧭 Two traps, and the provider warns you about one of them

**`execution_mode` on `tfe_workspace` is deprecated.** The provider says so, the
apply succeeds anyway, and the configuration will break at the next major
version. Execution settings have their own resource.

**The `cloud` block accepts no variables.** You already know this: the
`hcp-workspaces` lab established it, and here you reinvest it. The values to use
are the ones `terraform output` gives you in `plateforme/`.

## 🔎 What to look at while it runs

The apply in `application/` prints a URL. Open it: you will see the run you just
triggered, its logs, its plan, and the button you would have used had you
confirmed from the UI rather than from the CLI.

## 🧹 The check tidies up

`dsoxlab check` destroys the project and workspace it created. To validate again,
replay both applies: they take about thirty seconds each.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-premier-run-distant
```

Nine tests, all reading the **HCP Terraform API**. The central one looks for a
run in the `applied` state: a `terraform apply` played locally, unattached,
leaves no trace there.

Stuck? `dsoxlab hint hcp-terraform-premier-run-distant`.
