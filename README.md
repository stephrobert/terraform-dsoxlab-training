# Terraform Training: Associate & Professional 2026

Public hands-on Terraform course from the blog
[blog.stephane-robert.info](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/parcours/).

Each lab is self-contained: a guided tutorial (aligned with a course guide) plus
a challenge whose final state is proven by `pytest`. This repository is a **lab
provider** for the [`dsoxlab`](https://pypi.org/project/dsoxlab/) CLI.

> **No VM, no control node.** Unlike Ansible, Terraform runs on the learner's own
> machine: every lab is a `shell` lab, no `dsoxlab provision`. You write HCL and
> run `terraform` locally.

> **Lab folders are named in English** (English is the primary language of this
> repo). Lab content stays bilingual: `README.md`/`scenario.md`/`challenge` in
> English, `*.fr.md` for French.

> **Status: scenarios written, tests being added.** `meta.yml` declares the order
> of 10 sections / 87 labs. The first 8 sections follow the blog course (one lab
> per guide); the last two prepare the certifications, including **6 capstones
> aligned with the 6 Professional exam objectives**.

## Requirements

Depending on the labs you play:

- **`terraform` (or `tofu`) on the PATH**: all labs.
- **`libvirtd` + the `dmacvicar/libvirt` provider**: the `first-infra` section
  only (it provisions real local resources).
- **Docker + [Floci](https://blog.stephane-robert.info/docs/cloud/aws/floci/)**
  (local MIT AWS emulator, container `floci/floci:1.6.0` on `:4566`): the `aws`
  section and the write-only lab only. The `hashicorp/aws` provider targets Floci
  through an `endpoints` block, so zero AWS account and zero bill. Labs that
  declare a `runtime.services` block start Floci automatically under
  `dsoxlab run/check`.
- **An HCP Terraform token**: **no lab requires one.** The seven
  `hcp-terraform` labs deliberately stop just short of authentication, which is
  what makes them verifiable anywhere. A token is only needed to go further, and
  [`docs/hcp-token.md`](./docs/hcp-token.md) covers creating it, where to put it,
  and which location wins when several are filled.

```bash
uv tool install dsoxlab          # the CLI that drives the labs

python3 scripts/diagnostic-jeton-hcp.py --verifier   # where your token is, if any
```

## Usage

```bash
cd terraform-training
dsoxlab list-labs                # the 87-lab catalog
dsoxlab run <lab-id>             # play a lab (in challenge/work)
dsoxlab check <lab-id>           # validate with pytest
```

Trainer-side, replay every reference solution against its own tests:

```bash
scripts/test-all.sh              # plays all labs (needs .vault-pass)
scripts/verify-solutions.py      # replays solutions in isolated temp dirs
scripts/render-readme.py         # regenerate the lab list below (EN + FR)
```

## Labs

<!-- LABS_LIST_START -->

**87 labs** across **10 sections** (source of truth: [`meta.yml`](./meta.yml)).

### Discover Terraform

First contact: declarative vs imperative, OpenTofu, installation, CLI, workflow, providers/resources/data sources, project structure.

- [`terraform overview`](./labs/getting-started/terraform-overview/)
- [`declarative vs imperative`](./labs/getting-started/declarative-vs-imperative/)
- [`terraform vs opentofu`](./labs/getting-started/terraform-vs-opentofu/)
- [`install terraform`](./labs/getting-started/install-terraform/)
- [`cli terraform`](./labs/getting-started/cli-terraform/)
- [`terraform workflow`](./labs/getting-started/terraform-workflow/)
- [`providers resources data sources`](./labs/getting-started/providers-resources-data-sources/)
- [`terraform project structure`](./labs/getting-started/terraform-project-structure/)

### First infrastructures

Provision for real: first infra, variables/outputs, virtual network, libvirt VM, calling Ansible, debugging an apply, clean destroy.

- [`first infrastructure`](./labs/first-infra/first-infrastructure/)
- [`variables outputs`](./labs/first-infra/variables-outputs/)
- [`virtual network`](./labs/first-infra/virtual-network/)
- [`vm libvirt`](./labs/first-infra/vm-libvirt/)
- [`ansible`](./labs/first-infra/ansible/)
- [`debug apply`](./labs/first-infra/debug-apply/)
- [`clean destroy`](./labs/first-infra/clean-destroy/)

### Writing Terraform code

The HCL language in depth: providers, resources, variables, outputs, locals, data sources, expressions, functions, conditionals, count, for_each, for loops, dynamic blocks, depends_on, lifecycle, tfvars, version constraints, style, sensitive data.

- [`providers`](./labs/write-code/providers/)
- [`declare resources`](./labs/write-code/declare-resources/)
- [`variables`](./labs/write-code/variables/)
- [`outputs`](./labs/write-code/outputs/)
- [`locals`](./labs/write-code/locals/)
- [`data sources`](./labs/write-code/data-sources/)
- [`expressions`](./labs/write-code/expressions/)
- [`functions`](./labs/write-code/functions/)
- [`provider defined functions`](./labs/write-code/provider-defined-functions/)
- [`conditionals`](./labs/write-code/conditionals/)
- [`validation check preconditions`](./labs/write-code/validation-check-preconditions/)
- [`count`](./labs/write-code/count/)
- [`for each`](./labs/write-code/for-each/)
- [`for loops`](./labs/write-code/for-loops/)
- [`dynamic blocks`](./labs/write-code/dynamic-blocks/)
- [`depends on`](./labs/write-code/depends-on/)
- [`lifecycle`](./labs/write-code/lifecycle/)
- [`tfvars files`](./labs/write-code/tfvars-files/)
- [`version constraints`](./labs/write-code/version-constraints/)
- [`style guide`](./labs/write-code/style-guide/)
- [`sensitive values`](./labs/write-code/sensitive-data/sensitive-values/)
- [`ephemeral values`](./labs/write-code/sensitive-data/ephemeral-values/)
- [`write only arguments`](./labs/write-code/sensitive-data/write-only-arguments/)
- [`vault secrets`](./labs/write-code/sensitive-data/vault-secrets/)

### Terraform State

Understand and manipulate the state: backends, locking, terraform state list/show/mv/rm, backup/restore, diagnosis.

- [`understand state`](./labs/state/understand-state/)
- [`backends`](./labs/state/backends/)
- [`state locking`](./labs/state/state-locking/)
- [`terraform state list`](./labs/state/terraform-state-list/)
- [`terraform state show`](./labs/state/terraform-state-show/)
- [`terraform state mv`](./labs/state/terraform-state-mv/)
- [`terraform state rm`](./labs/state/terraform-state-rm/)
- [`removed block`](./labs/state/removed-block/)
- [`backup restore state`](./labs/state/backup-restore-state/)
- [`diagnose state`](./labs/state/diagnose-state/)

### Terraform Modules

Factor out with modules: creation, structure, variables/outputs, local module, registry, versioning, tests, best practices and anti-patterns.

- [`create modules`](./labs/modules/create-modules/)
- [`module structure`](./labs/modules/module-structure/)
- [`module variables outputs`](./labs/modules/module-variables-outputs/)
- [`module local`](./labs/modules/module-local/)
- [`module registry`](./labs/modules/module-registry/)
- [`version modules`](./labs/modules/version-modules/)
- [`test module`](./labs/modules/test-module/)
- [`module best practices`](./labs/modules/module-best-practices/)
- [`module anti patterns`](./labs/modules/module-anti-patterns/)

### Environments

Organize several environments: repo structure, dev/staging/prod separation, per-environment variables, workspaces (and when to use them), monorepo vs repo per stack.

- [`organize terraform repo`](./labs/environments/organize-terraform-repo/)
- [`separate environments`](./labs/environments/separate-environments/)
- [`per environment variables`](./labs/environments/per-environment-variables/)
- [`workspace`](./labs/environments/workspace/)
- [`when to use workspaces`](./labs/environments/when-to-use-workspaces/)
- [`monorepo vs repo per stack`](./labs/environments/monorepo-vs-repo-per-stack/)
- [`terraform in automation`](./labs/environments/terraform-in-automation/)

### Terraform on AWS (via Floci)

Apply Terraform to a real cloud provider emulated locally by Floci: first EC2, security group/subnet/instance, IAM, S3 remote-state backend, launch template + autoscaling, import/moved/drift. Feeds the Professional capstones (objectives 1 and 5).

- [`provider aws first ec2`](./labs/aws/provider-aws-first-ec2/)
- [`sg subnet instance`](./labs/aws/sg-subnet-instance/)
- [`iam role policy instance profile`](./labs/aws/iam-role-policy-instance-profile/)
- [`backend s3 remote state`](./labs/aws/backend-s3-remote-state/)
- [`launch template autoscaling`](./labs/aws/launch-template-autoscaling/)
- [`import moved drift`](./labs/aws/import-moved-drift/)

### HCP Terraform

The HashiCorp platform (Professional objective 6, assessed by MCQ): run workflow, workspaces and access management, credentials and dynamic credentials, policy as code and governance.

- [`hcp terraform overview`](./labs/hcp-terraform/hcp-terraform-overview/)
- [`hcp workspaces`](./labs/hcp-terraform/hcp-workspaces/)
- [`remote runs`](./labs/hcp-terraform/remote-runs/)
- [`variable sets`](./labs/hcp-terraform/variable-sets/)
- [`shared credentials`](./labs/hcp-terraform/shared-credentials/)
- [`projects teams`](./labs/hcp-terraform/projects-teams/)
- [`policy as code`](./labs/hcp-terraform/policy-as-code/)

### Associate Certification (004)

Prepare the Associate 004 exam (MCQ): essential commands and a mock exam.

- [`essential commands`](./labs/certifications/associate/essential-commands/)
- [`mock 004`](./labs/certifications/associate/mock-004/)

### Professional Certification (capstones by objective)

One capstone lab per objective of the Terraform Authoring and Operations Professional exam (the highest, hands-on level), plus a 4h integrative mock.

- [`capstone1 resource lifecycle`](./labs/certifications/professional/capstone1-resource-lifecycle/)
- [`capstone2 dynamic config`](./labs/certifications/professional/capstone2-dynamic-config/)
- [`capstone3 collaborative workflows`](./labs/certifications/professional/capstone3-collaborative-workflows/)
- [`capstone4 modules`](./labs/certifications/professional/capstone4-modules/)
- [`capstone5 providers`](./labs/certifications/professional/capstone5-providers/)
- [`capstone6 hcp`](./labs/certifications/professional/capstone6-hcp/)
- [`mock pro`](./labs/certifications/professional/mock-pro/)

<!-- LABS_LIST_END -->

The exact order is the **source of truth** in [`meta.yml`](meta.yml).

## Professional exam alignment

Section 10 breaks the [Terraform Authoring and Operations Professional exam
review](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
down into one capstone lab per objective:

| Exam objective | Capstone | Draws from |
|---|---|---|
| 1. Manage resource lifecycle | `capstone1-resource-lifecycle` | aws (Floci), state |
| 2. Develop & troubleshoot dynamic config | `capstone2-dynamic-config` | write-code |
| 3. Develop collaborative workflows | `capstone3-collaborative-workflows` | state, environments |
| 4. Create/maintain/use modules | `capstone4-modules` | modules |
| 5. Configure & use providers | `capstone5-providers` | write-code, aws (Floci) |
| 6. Collaborate with HCP Terraform (MCQ) | `capstone6-hcp` | hcp-terraform |
| Integration of all 6 objectives (4h) | `mock-pro` | the whole course |
