# Scenario: the first remote run, for real

**Exam objective targeted: 6a and 6b, in practice rather than in theory.**

**This is the only lab in the catalog that requires an HCP Terraform account.** The other
seven stop just short of authentication, which is what makes them playable anywhere. This
one crosses that boundary, and it is optional for that reason. The free plan is enough, and
[`docs/hcp-token.md`](../../../docs/hcp-token.md) covers the token.

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
