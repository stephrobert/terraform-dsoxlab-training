# Provision the platform, then let it run your infrastructure

**This is the only lab in the catalog that requires an HCP Terraform account.**
The other seven deliberately stop just short of authentication, which is what
makes them playable anywhere. This one crosses that boundary, and it is optional
for that reason.

The free plan is enough. [`docs/hcp-token.md`](../../../docs/hcp-token.md) covers
creating the token and where to put it:

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

## Terraform provisions Terraform

The `tfe` provider drives HCP Terraform itself: organizations, projects,
workspaces, variables, teams. It is infrastructure as code applied to the
platform that runs your infrastructure as code, and the mental leap is worth
making once.

```hcl
resource "tfe_workspace" "demo" {
  organization = data.tfe_organization.courante.name
  name         = var.workspace
  project_id   = tfe_project.formation.id
}
```

Without `project_id`, the workspace lands in the organization's default project,
and nothing tells you.

## The settings moved, and the warning does not stop you

Measured on 2026-09-25 with provider 0.81:

```
Warning: Argument is deprecated

  with tfe_workspace.essai,
  on main.tf line 30, in resource "tfe_workspace" "essai":
  30:   execution_mode = "remote"

Use resource `tfe_workspace_settings` to modify the workspace execution
settings. This attribute will be removed in a future release of the provider.
```

A warning does not stop an apply, and that is precisely what makes it dangerous:
the configuration works today and breaks at the provider's next major version,
without anyone having changed anything. Execution settings therefore live in
their own resource:

```hcl
resource "tfe_workspace_settings" "demo" {
  workspace_id   = tfe_workspace.demo.id
  execution_mode = "remote"
  auto_apply     = false
}
```

## What "remote" actually changes

With `execution_mode = "remote"`, `terraform apply` no longer computes anything
on your machine. It uploads an archive of the directory, HCP Terraform runs the
plan on a disposable VM, streams the logs back to your terminal, and keeps the
state.

Measured on 2026-09-25: a full remote run takes **about 30 seconds** on the free
plan, upload and teardown included.

Two consequences follow, and this lab makes you see both:

- the `message` variable is declared in the configuration **without a value**.
  The workspace supplies it at run time. Run the directory unattached and
  Terraform asks you for it; attached, it asks nothing;
- the state never touches your disk. `terraform output` reads it back over the
  network.

## Sensitivity travels further than you think

Also measured that day, and it surprised me:

```
Error: Output refers to sensitive values
  on main.tf line 34:
  34: output "empreinte_du_message" {
```

The output was `sha256(var.message)` — a fingerprint, which cannot be reversed.
Terraform does not look at what the function does: **anything derived from a
sensitive value is sensitive**, and a root output deriving from one must be
annotated. Note this applies to root outputs; the same expression in a resource
attribute goes through, as the `shared-credentials` lab shows.

## Over to you

```bash
dsoxlab run hcp-terraform-premier-run-distant
dsoxlab check hcp-terraform-premier-run-distant
dsoxlab hint hcp-terraform-premier-run-distant
```

Nine tests, all reading the **HCP Terraform API**: a local state would say what
you asked for, never what the platform did. The central one looks for a run in
the `applied` state, which nothing local can fabricate.

**The check tidies up**: it destroys the project and the workspace it created.
Leaving them behind in your account would be worse than replaying two
thirty-second applies.

Exam objectives targeted: **6a** and **6b**, in practice.

Reference: [the CLI-driven run workflow](https://developer.hashicorp.com/terraform/cloud-docs/run/cli)
