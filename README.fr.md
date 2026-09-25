# Formation Terraform : Associate & Professional 2026

Lab pédagogique public de la formation Terraform du blog
[blog.stephane-robert.info](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/parcours/).

Chaque lab est autonome : un tutoriel guidé (aligné sur un guide du parcours)
plus un challenge dont l'état final est prouvé par `pytest`. Ce dépôt est un
**fournisseur de labs** pour la CLI [`dsoxlab`](https://pypi.org/project/dsoxlab/).

> **Pas de VM, pas de control node.** Contrairement à Ansible, Terraform tourne
> sur la machine de l'apprenant : tous les labs sont de type `shell`, aucun
> `dsoxlab provision`. On écrit du HCL et on lance `terraform` en local.

> **Les dossiers de labs sont nommés en anglais** (l'anglais est la langue
> première du dépôt). Le contenu reste bilingue : `README.md`/`scenario.md`/
> `challenge` en anglais, les `*.fr.md` pour le français.

> **État : scénarios écrits, tests en cours d'écriture.** Le `meta.yml` déclare
> l'ordre des 10 sections / 88 labs. Les 8 premières sections suivent le parcours
> du blog (un lab par guide) ; les deux dernières préparent les certifications,
> dont **6 capstones alignés sur les 6 objectifs de l'examen Professional**.

## Prérequis

Selon les labs joués :

- **`terraform` (ou `tofu`) sur le PATH** : tous les labs.
- **`libvirtd` + provider `dmacvicar/libvirt`** : section `first-infra`
  uniquement (provision de vraies ressources en local).
- **Docker + [Floci](https://blog.stephane-robert.info/docs/cloud/aws/floci/)**
  (émulateur AWS local MIT, conteneur `floci/floci:1.6.0` sur `:4566`) : section
  `aws` et lab write-only uniquement. Le provider `hashicorp/aws` vise Floci via
  un bloc `endpoints`, donc zéro compte AWS et zéro facture. Les labs qui
  déclarent un bloc `runtime.services` démarrent Floci tout seuls sous
  `dsoxlab run/check`.
- **Un jeton HCP Terraform** : **un seul lab sur 88 en exige un**,
  `hcp-terraform/premier-run-distant`, qui fait tourner un vrai run distant et
  reste optionnel pour cette raison. Les sept autres labs `hcp-terraform`
  s'arrêtent volontairement juste avant l'authentification, et c'est ce qui les
  rend vérifiables partout. Sans jeton, le lab optionnel se **skippe** au lieu
  d'échouer. [`docs/hcp-token.fr.md`](./docs/hcp-token.fr.md) explique comment
  créer le jeton, où le poser, et lequel l'emporte quand plusieurs emplacements
  sont remplis.

```bash
uv tool install dsoxlab          # la CLI qui pilote les labs

python3 scripts/diagnostic-jeton-hcp.py --verifier   # où est votre jeton, s'il y en a un
```

## Utilisation

```bash
cd terraform-training
dsoxlab list-labs                # catalogue des 88 labs
dsoxlab run <lab-id>             # dérouler un lab (dans challenge/work)
dsoxlab check <lab-id>           # valider par pytest
```

Côté formateur, rejouer chaque solution de référence contre ses propres tests :

```bash
scripts/test-all.sh              # joue tous les labs (nécessite .vault-pass)
scripts/verify-solutions.py      # rejoue les solutions dans des dossiers temporaires isolés
scripts/render-readme.py         # régénère la liste des labs ci-dessous (EN + FR)
```

## Labs

<!-- LABS_LIST_START -->

**88 labs** répartis en **10 sections** (source de vérité : [`meta.yml`](./meta.yml)).

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
- [`premier run distant`](./labs/hcp-terraform/premier-run-distant/)

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

L'ordre exact est la **source de vérité** dans [`meta.yml`](meta.yml).

## Alignement sur l'examen Professional

La section 10 décline la [liste de contenu de l'examen Terraform Authoring and
Operations Professional](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
en un capstone par objectif :

| Objectif d'examen | Capstone | Provient de |
|---|---|---|
| 1. Manage resource lifecycle | `capstone1-resource-lifecycle` | aws (Floci), state |
| 2. Develop & troubleshoot dynamic config | `capstone2-dynamic-config` | write-code |
| 3. Develop collaborative workflows | `capstone3-collaborative-workflows` | state, environments |
| 4. Create/maintain/use modules | `capstone4-modules` | modules |
| 5. Configure & use providers | `capstone5-providers` | write-code, aws (Floci) |
| 6. Collaborate with HCP Terraform (QCM) | `capstone6-hcp` | hcp-terraform |
| Intégration des 6 objectifs (4h) | `mock-pro` | tout le parcours |
