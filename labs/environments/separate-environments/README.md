# Two directories, two backends, two sets of permissions

Separating `dev` from `prod` with two directories is not a tidiness preference. It
is the only layout that allows **two sets of credentials** and **two independent
states**, and it is what the documentation explicitly recommends for distinct
deployments: "separate Terraform configurations that correspond to architectural
boundaries", combined with reusable modules for the shared code.

## The argument that counts, and it is not ergonomics

You often read that **workspaces** should be avoided because a forgotten
`terraform workspace select` can destroy the wrong environment. True, but
secondary. The official argument is **structural**:

> Workspaces are not appropriate for system decomposition or deployments requiring
> separate credentials and access controls.

The reason fits in one sentence: "CLI workspaces within a working directory use the
**same backend**". One backend, therefore one set of accesses. A production that
must authenticate with a **role** different from `dev` cannot live in a CLI
workspace, however disciplined the team.

## The layout: one module, two roots

```text
depot/
├── modules/plaque/       ← the shared code, written ONCE
├── envs/dev/             ← root, its own backend and state
├── envs/prod/            ← root, its own backend and state
└── etats/                ← both state files
```

Each root calls the module by a **relative path**, with its own values:

```hcl
module "plaques" {
  source = "../../modules/plaque"

  environnement = "prod"
  repliques     = 3
}
```

## Why the `backend` block is empty

The natural reflex would be to parameterise the state path with a variable. It is
**forbidden**:

```text
Error: Variables not allowed

  on main.tf line 12, in terraform:
  12:     path = "../etats/${var.env}.tfstate"

Variables may not be used here.
```

"A backend block cannot refer to named values (like input variables, locals, or
data source attributes)." Two ways out then: **duplicate** the backend file in each
root, or use **partial configuration**.

## Partial configuration, in practice

The block stays **empty**, hence **identical** everywhere:

```hcl
terraform {
  backend "local" {}
}
```

And the missing arguments are supplied at **initialisation**:

```bash
# in envs/prod
terraform init -backend-config=backend-prod.hcl
```

```hcl
# envs/prod/backend-prod.hcl
path = "../../etats/prod.tfstate"
```

The documentation gives three forms: a **file** via `-backend-config=PATH`, pairs
via `-backend-config="KEY=VALUE"`, or **interactive** entry. It is the most widely
used pattern in automation, because it keeps the code **identical** from one
environment to the next.

Terraform then records the retained configuration in
`.terraform/terraform.tfstate`: that is where you check, without guessing, which
state a root really drives.

```bash
jq '.backend.config.path' .terraform/terraform.tfstate
```

## What the separation guarantees

A `terraform destroy` in `envs/dev` cannot touch `envs/prod`: the command only acts
on its own root's state, and the two states are distinct. The property is
**verified**, not assumed:

```bash
cd envs/dev && terraform destroy -auto-approve
cd ../prod && terraform show -json | jq '.values.root_module'
```

The second must be **intact**. That is exactly what this lab's validation does, in
a copy of the work.

## Two remote-backend traps

On a shared backend, two points are missing from many examples. **Locking** first:
the S3 backend documents `use_lockfile`, whose default is **`false`**, and DynamoDB
locking is now **deprecated**. A team backend without a lock means two concurrent
applies and a corrupted state.

**Changing** the backend next: "When you change a backend's configuration, you must
run `terraform init` again". Terraform then offers to **migrate** the state, which
is precisely the move from a local lab to a remote backend.

## Your turn

You know why two directories beat two workspaces, why a `backend` block takes no
variable, how partial configuration solves it, and how to prove isolation. The
challenge has you wire two roots onto a shared module, then destroy dev and watch
prod hold.

```bash
dsoxlab run environments-separate-environments
dsoxlab check environments-separate-environments
dsoxlab hint environments-separate-environments
```

It runs **offline**, with the `local` backend.

Target exam sub-objective: **3b** (backends and partial configuration).

Reference: [separating dev, staging and prod](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/separer-environnements/)
