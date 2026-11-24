# The first remote run, for real

## The situation

**Exam objective targeted: 6a and 6b, in practice rather than in theory.**

**This is the only lab in the catalog that requires an HCP Terraform account.** The other
seven stop just short of authentication, which is what makes them playable anywhere. This
one crosses that boundary, and it is optional for that reason. The free plan is enough, and
[`docs/hcp-token.md`](../../../../docs/hcp-token.md) covers the token.

A team has been told its next deployments will run on HCP Terraform. Nobody has ever seen
one: the platform is a page in a browser, and the connection between that page and a
`terraform apply` is unclear.

## Capability targeted

Provision the platform itself with Terraform — project, workspace, execution settings, a
variable that lives in the workspace — then attach a configuration to that workspace and
have a run execute on HashiCorp's infrastructure rather than on your machine.

## Where the learner starts

`challenge/work` holds two directories:

1. `plateforme/`, which drives HCP Terraform through the `tfe` provider. Four `???` to
   fill, and one organization name to supply in `organisation.auto.tfvars`.
2. `application/`, an ordinary configuration whose `cloud` block is missing. It creates a
   `random_pet`: what matters is not the resource, it is **where it is computed**.

## The state to reach

1. A `formation-terraform` project exists in the organization.
2. A `premier-run-distant` workspace exists **in that project**, in `remote` execution mode
   and with auto-apply off.
3. A `message` variable exists in the workspace, of category `terraform`, marked sensitive.
4. `application/` is attached to that workspace by a `cloud` block written out in full.
5. A run has been **applied** on that workspace, and the remote state carries
   `preuve_du_run`.

## The two traps, both measured

**`execution_mode` on `tfe_workspace` is deprecated.** Measured on 2026-09-25 with provider
0.81:

```
Warning: Argument is deprecated
Use resource `tfe_workspace_settings` to modify the workspace execution settings.
This attribute will be removed in a future release of the provider.
```

A warning does not stop an apply, and that is exactly what makes it dangerous: the
configuration works today and breaks at the provider's next major version, without anyone
having changed anything.

**Sensitivity propagates through functions.** Also measured that day: `sha256(var.message)`
is still considered sensitive, and a root output deriving from it must be annotated, even
though a fingerprint cannot be reversed. Terraform does not look at what the function does.

## How it is proven

The tests query the **HCP Terraform API**, not the local state. A local state would say what
the learner asked for, never what the platform did.

The central test looks for a run in the `applied` state on the created workspace: nothing
local can fabricate that. Another reads the remote state version and its outputs, which
only exist because the run computed them over there.

The teardown destroys everything the lab created in the organization. Leaving a project and
a workspace behind in someone's account is worse than asking them to replay two
thirty-second applies, and a lab that does not tidy up has no place here.

## 🎯 Challenge: make a run execute at HashiCorp

### ⚠️ The only lab that needs an account

The other seven `hcp-terraform` labs need nothing. This one needs an HCP
Terraform account — the free plan is enough — and an API token on your machine:

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

Without a token the tests **skip**: you will not see red, you will see where to
find what is missing. The guide is [`docs/hcp-token.md`](../../../../docs/hcp-token.md).

### 📦 Starting point

| File | State |
| --- | --- |
| `plateforme/organisation.auto.tfvars` | one `???`: **your** organization |
| `plateforme/plateforme.tf` | four `???` |
| `plateforme/versions.tf`, `variables.tf` | **supplied** |
| `application/versions.tf` | the `cloud` block is missing |
| `application/main.tf` | **supplied**, do not change |

### ✅ Objective

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

### 🧭 Two traps, and the provider warns you about one of them

**`execution_mode` on `tfe_workspace` is deprecated.** The provider says so, the
apply succeeds anyway, and the configuration will break at the next major
version. Execution settings have their own resource.

**The `cloud` block accepts no variables.** You already know this: the
`hcp-workspaces` lab established it, and here you reinvest it. The values to use
are the ones `terraform output` gives you in `plateforme/`.

### 🔎 What to look at while it runs

The apply in `application/` prints a URL. Open it: you will see the run you just
triggered, its logs, its plan, and the button you would have used had you
confirmed from the UI rather than from the CLI.

### 🧹 The check tidies up

`dsoxlab check` destroys the project and workspace it created. To validate again,
replay both applies: they take about thirty seconds each.

### 🔍 Validation

```bash
dsoxlab check hcp-terraform-premier-run-distant
```

Nine tests, all reading the **HCP Terraform API**. The central one looks for a
run in the `applied` state: a `terraform apply` played locally, unattached,
leaves no trace there.

Stuck? `dsoxlab hint hcp-terraform-premier-run-distant`.
