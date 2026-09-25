# Terraform Training: Associate & Professional 2026

**Language:** [English](./README.md) · [Français](./README.fr.md)

[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/terraform-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/terraform-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/terraform-training.svg)](https://score.getplumber.io/github.com/stephrobert/terraform-training)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Hands-on **Terraform** training, driven by the
[`dsoxlab`](https://github.com/stephrobert/dsoxlab) CLI. This repository is the
**lab catalog** behind the Terraform track of
[blog.stephane-robert.info](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/parcours/),
geared toward the **Terraform Associate (004)** and **Terraform Authoring and
Operations Professional** certifications.

## What it is

`terraform-training` is a **content repository**, not an application. It
provides:

- **guided labs** whose brief describes a situation, never a set of steps;
- **challenges** with no step-by-step, to test autonomy;
- **capstones** aligned with the six objectives of the Professional exam;
- **automated validation** that proves the state the configuration computes, not
  that a command was typed;
- **scoring** with cost-weighted hints.

The `dsoxlab` CLI is the single entry point: it sets a lab up, shows the brief,
validates, scores and reports. It lives in **its own repository** and is
installed **separately**.

## Requirements

- Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)
- `git`
- **`terraform` (or `tofu`) on the PATH**: every lab.
- **`libvirtd` and the `dmacvicar/libvirt` provider**: the `first-infra` section
  only, which provisions real local resources.
- **Docker and [Floci](https://blog.stephane-robert.info/docs/cloud/aws/floci/)**,
  a local MIT-licensed AWS emulator (`floci/floci:1.6.0`): the `aws` section and
  a few AWS-targeting labs. The `hashicorp/aws` provider points at Floci through
  an `endpoints` block: no AWS account, no bill. Those labs declare Floci in
  `runtime.services`, and dsoxlab starts it for you.
- **Docker**, for the `vault-secrets` lab: it starts a `hashicorp/vault:1.21`
  server in development mode, declared the same way.
- **An HCP Terraform token**: **exactly one lab out of 88 requires one**, and it
  is optional. Without a token its tests skip instead of failing. See
  [`docs/hcp-token.md`](./docs/hcp-token.md).

No VM, no `dsoxlab provision`: unlike the Ansible and Linux catalogs, Terraform
runs on the learner's own machine. Every lab is `runtime: shell`.

## Install

`dsoxlab` is published on [PyPI](https://pypi.org/project/dsoxlab/). Install it
as a standalone tool:

```bash
# 1. Install the dsoxlab CLI (external tool, stays out of this repo)
uv tool install dsoxlab        # or: pipx install dsoxlab

# 2. Clone this lab catalog
git clone https://github.com/stephrobert/terraform-training.git
cd terraform-training

# 3. Check the contract is valid
dsoxlab validate-structure
```

### Your first lab, in five minutes

```bash
dsoxlab list-labs                                     # browse the catalog
dsoxlab run       getting-started-terraform-workflow  # set the starting state
dsoxlab challenge getting-started-terraform-workflow  # read the mission
# ... you work in challenge/work ...
dsoxlab check     getting-started-terraform-workflow  # validate and score
```

`run` creates the lab's work directory and copies the declared fixtures into it.
Everything then happens in `challenge/work`: it is the only place you change,
and `dsoxlab clean` removes it.

Stuck? `dsoxlab hint <id>` reveals a hint, whose cost is deducted from the score.

### Keeping it up to date

```bash
git pull                       # the catalog
uv tool upgrade dsoxlab        # the engine
```

The two evolve separately. A lab that fails after a Terraform upgrade is a defect
in the catalog: open an issue, and `dsoxlab support --issue` arrives pre-filled.

## How it works

### The declarative contract (two levels)

The catalog is described by data, not code, which keeps the `dsoxlab` engine
domain-agnostic:

- **`meta.yml`** at the root declares the repository identity and the **order**
  of the sections shown by `list-labs`;
- **`lab.yaml`** per lab declares its `skills`, `level`, `runtime` (type,
  fixtures, services), `distros`, `doc_url` and a `validation` block. A
  `lab.fr.yaml` overrides `title` and `description` in French, and nothing else.

`dsoxlab validate-structure` checks the whole contract: `meta.yml` is well
formed, every referenced lab exists with a valid `lab.yaml`, every declared test
and fixture file is really there, and every relative link in a README leads
somewhere.

### The lab lifecycle

```bash
dsoxlab list-labs              # browse the catalog
dsoxlab show      <id>         # metadata and status of one lab
dsoxlab run       <id>         # set the starting state
dsoxlab challenge <id>         # read the mission, no step-by-step
dsoxlab hint      <id>         # reveal a hint (deducted from the score)
dsoxlab check     <id>         # run the tests, compute and record the score
dsoxlab clean     <id>         # remove the work directory
dsoxlab progress               # per-section progress, average score
```

### Runtimes

| Runtime | What the lab asks for |
|---|---|
| `shell` | a terminal and `terraform`. The tests read the state your configuration computes, on your own machine. |
| `shell` + `floci` | Docker as well: dsoxlab starts the AWS emulator declared in `runtime.services`, and stops it with the session. |
| `shell` + HCP account | a single, optional lab, which runs a real remote run on HCP Terraform. |

### The validation model

Validation **proves the state, it does not trust the learner**. Each lab ships
`pytest` tests under `challenge/tests/` that query `terraform show -json` and
`terraform output -json`: what the configuration COMPUTES, never what a file
contains.

And a lab is proven **in both directions**: the tests must fail before the work
and pass after it. A test that is green before the work is not a test, it is an
assumption about the setup. The root `conftest.py` replays the reference solution
before the tests in instructor mode, to prove the solution itself is correct;
`dsoxlab check` goes through the learner's path instead.

Reference solutions live under `solution/`, **encrypted with ansible-vault**: a
solution shipped in clear text spoils the lab, and git keeps it forever.

### Scoring, hints, progress

`check` records a score (tests passed out of total, minus the cost of any hints
revealed). Hints are **base64-encoded** in `challenge/hints.yaml`, so that
opening the file does not give them away, and their cost grows with their
precision. History lives in a SQLite database **local to this repository**.

## Catalog

Labs live under `labs/` and are ordered by `meta.yml`. The table below is
generated from the real `lab.yaml` files: run `python3 scripts/gen_catalog.py`
to refresh it.

<!-- LABS:START -->
### Discover Terraform

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `getting-started-terraform-overview` | Prove that Terraform has a memory | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/presentation-terraform/) |
| `getting-started-declarative-vs-imperative` | Prove idempotence where the imperative script diverges | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/declaratif-vs-imperatif/) |
| `getting-started-terraform-vs-opentofu` | Prove Terraform / OpenTofu compatibility, and where it stops | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/terraform-vs-opentofu/) |
| `getting-started-install-terraform` | Pin the CLI version and lock the providers | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/installer-terraform/) |
| `getting-started-cli-terraform` | Make fmt, validate and the outputs agree | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/cli-terraform/) |
| `getting-started-terraform-workflow` | Read a plan before applying it | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/workflow-terraform/) |
| `getting-started-providers-resources-data-sources` | What Terraform manages, and what it merely reads | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/providers-resources-data-sources/) |
| `getting-started-terraform-project-structure` | Split a monolith without moving the plan | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/structure-projet-terraform/) |

### First infrastructures

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `first-infra-first-infrastructure` | First infrastructure: the full cycle, proven | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/premiere-infrastructure/) |
| `first-infra-variables-outputs` | Variables, locals and the real precedence order | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/variables-outputs/) |
| `first-infra-virtual-network` | The dependency Terraform cannot guess | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/reseau-virtuel/) |
| `first-infra-vm-libvirt` | Update in place or replacement: read it in the plan | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/vm-libvirt/) |
| `first-infra-ansible` | Produce an Ansible inventory from the state | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/ansible/) |
| `first-infra-debug-apply` | Resume after a failed apply, without redoing the work | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/debug-apply/) |
| `first-infra-clean-destroy` | Destroying cleanly, and the four things it covers | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/destroy-propre/) |

### Writing Terraform code

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `write-code-providers` | Explicit source and provider alias | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/providers-terraform/) |
| `write-code-declare-resources` | Read a resource's lifecycle in the plan | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/declarer-ressources/) |
| `write-code-variables` | Variables typing, validation and precedence | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/variables-terraform/) |
| `write-code-outputs` | The secret the output does not hide | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/outputs-terraform/) |
| `write-code-locals` | The local that is not resolved at plan time | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/locals-terraform/) |
| `write-code-data-sources` | When exactly does Terraform read a data source? | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/data-sources/) |
| `write-code-expressions` | What expressions really compute | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/expressions-terraform/) |
| `write-code-functions` | Compose values with HCL functions | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fonctions-terraform/) |
| `write-code-provider-defined-functions` | Provider-defined functions | l2 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/provider-defined-functions/) |
| `write-code-conditionals` | The configuration that refuses absurd values | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/conditions-terraform/) |
| `write-code-validation-check-preconditions` | Custom conditions: precondition, postcondition and check blocks | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/custom-conditions/) |
| `write-code-count` | count indexes by position, and the position lies | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/count-terraform/) |
| `write-code-for-each` | Add an instance without destroying the others | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/for-each-terraform/) |
| `write-code-for-loops` | Transform a catalog with for expressions | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/boucles-for-terraform/) |
| `write-code-dynamic-blocks` | Generate blocks, and know when not to | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/blocs-dynamiques/) |
| `write-code-depends-on` | depends_on belongs only where a reference cannot go | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/depends-on/) |
| `write-code-lifecycle` | The lifecycle block decides the order, not you | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/lifecycle-terraform/) |
| `write-code-tfvars-files` | The typo that breaks nothing | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fichiers-tfvars/) |
| `write-code-version-constraints` | Version constraints and the lock file | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/version-constraints-terraform/) |
| `write-code-style-guide` | The config that works but no CI accepts | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/style-guide-terraform/) |
| `write-code-sensitive-data-sensitive-values` | When sensitivity breaks for_each | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/sensitive-terraform/) |
| `write-code-sensitive-data-ephemeral-values` | The value that never touches the state | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/ephemeral-values/) |
| `write-code-sensitive-data-write-only-arguments` | Write-only arguments: a secret that never lands in the state | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/write-only-arguments/) |
| `write-code-sensitive-data-vault-secrets` | Read secrets from Vault | l2 | TF-PROFESSIONAL | shell + vault | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/vault-secrets/) |

### Terraform State

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `state-understand-state` | Take over a secret already in service, without regenerating it | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/comprendre-state/) |
| `state-backends` | Migrate the state without breaking its lineage | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/backends-terraform/) |
| `state-state-locking` | State locking, what it really blocks | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/verrouillage-state/) |
| `state-terraform-state-list` | terraform state list, the address is the identity | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-list/) |
| `state-terraform-state-show` | terraform state show, ce que la fiche cache | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-show/) |
| `state-terraform-state-mv` | terraform state mv and the moved block, refactor without destroying | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-mv/) |
| `state-terraform-state-rm` | terraform state rm and the removed block, stop managing without destroying | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-rm/) |
| `state-removed-block` | The removed block: bequeath an infrastructure without destroying it | l2 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/bloc-removed/) |
| `state-backup-restore-state` | Restore an amputated state: pick the right backup, prove nothing was recreated | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/sauvegarder-restaurer-state/) |
| `state-diagnose-state` | Diagnose a drift and adopt an orphan resource, without losing its value | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/diagnostiquer-state/) |

### Terraform Modules

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `modules-create-modules` | A reusable module configures no provider of its own | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/creation-modules/) |
| `modules-module-structure` | Refactor a monolith into the standard module structure | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/structure-module/) |
| `modules-module-variables-outputs` | A module interface is a contract, not just types | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/variables-outputs-module/) |
| `modules-module-local` | A local module is read in place, not installed | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/module-local/) |
| `modules-module-registry` | A registry module is downloaded, versioned, and never locked | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/module-registry/) |
| `modules-version-modules` | Publish and consume module versions with Git tags | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/versionner-modules/) |
| `modules-test-module` | Prove a module with terraform test, mutations included | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/tester-module/) |
| `modules-module-best-practices` | Make a module composable, and prove it from the plan JSON | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/bonnes-pratiques-modules/) |
| `modules-module-anti-patterns` | Refactor a copy-pasted project without destroying anything | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/anti-patterns-modules/) |

### Environments

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `environments-organize-terraform-repo` | Split a monolithic configuration, and prove the plan did not move | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/organiser-repo-terraform/) |
| `environments-separate-environments` | Two roots, two states, one shared module | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/separer-environnements/) |
| `environments-per-environment-variables` | Which value wins, and how to prove it | l3 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/variables-par-environnement/) |
| `environments-workspace` | One directory, three states that never see each other | l3 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/workspace/) |
| `environments-when-to-use-workspaces` | Workspaces or separate configurations, and what the split costs | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/quand-utiliser-workspaces/) |
| `environments-monorepo-vs-repo-per-stack` | Split a monorepo into two stacks that talk to each other | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/monorepo-vs-repo-par-stack/) |
| `environments-terraform-in-automation` | Run Terraform in automation (CI/CD) | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/terraform-en-automation/) |

### Terraform on AWS (via Floci)

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `aws-provider-aws-first-ec2` | AWS provider: authentication, endpoints and default tags | l3 | TF-ASSOCIATE | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/provider-aws-premiere-ec2/) |
| `aws-sg-subnet-instance` | Security group: dedicated rules, for_each and a deterministic subnet | l3 | TF-ASSOCIATE | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/sg-subnet-instance/) |
| `aws-iam-role-policy-instance-profile` | Compose the IAM chain, and name its two policies correctly | l3 | TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/iam-role-policy-instance-profile/) |
| `aws-backend-s3-remote-state` | A remote state, locked, and read by another stack | l3 | TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/backend-s3-remote-state/) |
| `aws-launch-template-autoscaling` | Read a replacement in the plan, before it happens | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/launch-template-autoscaling/) |
| `aws-import-moved-drift` | Import, moved and drift: the three traps a tutorial never shows | l3 | TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/import-moved-drift/) |

### HCP Terraform

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `hcp-terraform-hcp-terraform-overview` | The run workflow: played in two steps, then qualified | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/presentation-hcp-terraform/) |
| `hcp-terraform-hcp-workspaces` | Workspaces: one word, two meanings, two attachment strategies | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/workspaces-hcp/) |
| `hcp-terraform-remote-runs` | The stream a run sends back, and the three ways to start one | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/remote-runs/) |
| `hcp-terraform-variable-sets` | Fifteen precedence levels, and one inversion | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/variable-sets/) |
| `hcp-terraform-shared-credentials` | Credentials: neither in the code, nor in the state | l3 | TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/credentials-partage/) |
| `hcp-terraform-projects-teams` | Permissions add up, they do not override | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/projects-equipes/) |
| `hcp-terraform-policy-as-code` | Policy as code: what blocks a run, and who can override it | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/policy-as-code/) |
| `hcp-terraform-premier-run-distant` | The first remote run, for real (optional, needs an account) | l3 | TF-PROFESSIONAL | shell + HCP account | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/remote-runs/) |

### Associate Certification (004)

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `certifications-associate-essential-commands` | The commands the exam expects, done rather than recited | l4 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/associate/) |
| `certifications-associate-mock-004` | Associate 004: mock exam | l4 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/associate/) |

### Professional Certification (capstones by objective)

| Lab (id) | Title | Level | Certif | Runtime | Companion guide |
|---|---|---|---|---|---|
| `certifications-professional-capstone1-resource-lifecycle` | Pro · Objective 1: resource lifecycle, import and drift reconciliation | l4 | TF-PROFESSIONAL | shell + floci | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone2-dynamic-config` | Pro · Objective 2: dynamic configuration and troubleshooting | l4 | TF-PROFESSIONAL | shell | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone3-collaborative-workflows` | Pro · Objective 3: collaborative workflows | l4 | TF-PROFESSIONAL | shell + floci | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone4-modules` | Pro · Objective 4: create, maintain and use modules | l4 | TF-PROFESSIONAL | shell | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone5-providers` | Pro · Objective 5: configure and use providers | l4 | TF-PROFESSIONAL | shell + floci | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone6-hcp` | Pro · Objective 6: HCP Terraform (multiple-choice) | l4 | TF-PROFESSIONAL | shell | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-mock-pro` | Pro · Integrative 4h mock exam | l4 | TF-PROFESSIONAL | shell | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |

_88 labs, table generated by `scripts/gen_catalog.py`._
<!-- LABS:END -->

## Contributing and license

Contributions are welcome: read [CONTRIBUTING.md](./CONTRIBUTING.md), which
describes the real anatomy of a lab in this repository and the golden rule, a
lab is proven in both directions. The [code of
conduct](./CODE_OF_CONDUCT.md) applies to every exchange, and vulnerabilities are
reported privately: [SECURITY.md](./SECURITY.md).

### License

This content is published under [Creative Commons Attribution 4.0
International](./LICENSE) (CC BY 4.0). You may share and adapt it, including
commercially, provided you credit the source.
