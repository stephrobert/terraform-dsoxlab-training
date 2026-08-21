# The criterion is not the environment, it is the backend

The "workspaces or separate configurations?" question is settled by a single
property, and it is **technical**, not organisational.

## The reason that explains everything else

A `backend` block **cannot reference any named value**. Measured:

```hcl
terraform {
  backend "local" {
    path = "etats/${terraform.workspace}.tfstate"
  }
}
```

```text
Error: Variables not allowed

  on main.tf line 3, in terraform:
   3:     path = "etats/${terraform.workspace}.tfstate"

Variables may not be used here.
```

`terraform.workspace` is therefore **unusable** in a backend. Every workspace in
a directory necessarily writes to the **same place**, with the **same** access
rights to the state.

## A `provider` block, on the other hand, accepts expressions

This is the asymmetry many guides miss, and it changes the conclusion. The
**same** `terraform.workspace`, inside a `provider` block:

```hcl
provider "tls" {
  proxy {
    url = "http://proxy-${terraform.workspace}.exemple.invalide:3128"
  }
}
```

Measured: `init` and `plan` both succeed, exit code **0**.

In other words, you **can** vary the role used to create resources per
workspace, exactly as the S3 backend documentation shows with
`assume_role = { role_arn = var.workspace_iam_roles[terraform.workspace] }`. What
you **cannot** vary is the **state storage** and the rights protecting it.

## What workspaces isolate, and what they do not

They isolate **state**. Not real objects. Three commands make the point:

```bash
terraform workspace new dev && terraform apply -auto-approve   # writes app.conf
terraform workspace new prod
terraform plan
```

```text
  # local_file.app will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

Yet `app.conf` is **still** on disk: `prod` does not see it, because it is not in
**its** state. An apply in `prod` **overwrites** it without ever having seen it.
Two workspaces targeting the same object therefore collide silently.

## Where workspaces remain the right tool

One infrastructure, **light variations**, same rights, same backend. The classic
pattern is a map indexed by workspace:

```hcl
locals {
  tailles = {
    default = 1
    dev     = 2
    prod    = 8
  }
}

output "taille" {
  value = lookup(local.tailles, terraform.workspace, local.tailles["default"])
}
```

Measured: `dev` returns **2**, `prod` returns **8**. The third argument of
`lookup` is the **fallback**, used when the workspace is absent from the map.

## What the split costs

Splitting into configurations is not free, and the documentation says so:
"Terraform installs a separate cache of plugins and modules for each working
directory." Measured on this lab, each working directory installs its own cache,
around **18 MB** here. Add to that updating and reinitialising **each** directory
separately.

## What about the data?

Once separated, two roots no longer talk to each other. The official bridge is
reading the other's **remote state**, through its **declared outputs**:

```hcl
data "terraform_remote_state" "socle" {
  backend = "local"

  config = {
    path = "../socle/terraform.tfstate"
  }
}
```

The documentation flags the trade-off: it "creates a tighter coupling between
configurations".

## Your turn

```bash
dsoxlab run environments-when-to-use-workspaces
dsoxlab check environments-when-to-use-workspaces
dsoxlab hint environments-when-to-use-workspaces
```

It runs **offline**, on the `local` and `random` providers.

Exam sub-objective covered: **3d**.

Reference: [when to use workspaces](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/quand-utiliser-workspaces/)
