# A workspace isolates state, and nothing else

A Terraform workspace gives the **same** configuration several instances of
**state**. That is all it does. It changes neither the backend, nor the
credentials, nor the working directory.

## Where the states live, and where the selection lives

On a local backend, `default` keeps its state at the root, and every other
workspace gets its own under `terraform.tfstate.d/`:

```text
terraform.tfstate                       <- default
terraform.tfstate.d/dev/terraform.tfstate
terraform.tfstate.d/prod/terraform.tfstate
```

The **selected** workspace is not part of the state: it is written to
`.terraform/environment`, a **local** file that is never shared.

```bash
cat .terraform/environment
```

Two people working on the same checkout can therefore sit on two **different**
workspaces without knowing it.

## Derive naming from `terraform.workspace`

This is the expression that lets one configuration serve several environments
without hard-coding a single name:

```hcl
resource "local_file" "app" {
  count = terraform.workspace == "prod" ? 3 : 1

  filename = "${path.root}/sorties/app-${terraform.workspace}-${count.index}.conf"
  content  = "environnement ${terraform.workspace} instance ${count.index}\n"
}
```

A **variable** would not do the same job: it keeps the same value from one
workspace to the next until you override it on every command.

## Deleting a workspace destroys nothing

This is the costliest trap. Terraform refuses while the workspace still tracks
resources:

```text
Error: Workspace is not empty

Workspace "bac-a-sable" is currently tracking the following resource instances:
  - local_file.app[0]
  - random_pet.temoin

Deleting this workspace would cause Terraform to lose track of any associated
remote objects, which would then require you to delete them manually outside
of Terraform.
```

The `-force` option overrides that check, and leaves **orphans** behind:

```text
Deleted workspace "bac-a-sable"!

WARNING: "bac-a-sable" was non-empty.
The resources managed by the deleted workspace may still exist,
but are no longer manageable by Terraform since the state has been deleted.
```

Measured: all three produced files are **still** on disk after a `-force`. The
correct order is **destroy**, then delete.

## The `default` workspace can never be deleted

Two different messages, depending on where you try from:

```text
Workspace "default" is your active workspace.
You cannot delete the currently active workspace.
```

And after switching away first, as many guides advise:

```text
Cannot delete the default workspace
```

So switching unblocks **nothing**: `default` simply cannot be deleted.

## `TF_WORKSPACE`, and its two side effects

It is the only way to select a workspace **without** changing the local
selection, which makes it the tool of choice for CI pipelines:

```bash
TF_WORKSPACE=prod terraform output
```

But while it is set, two commands **refuse** to run:

```text
The selected workspace is currently overridden using the TF_WORKSPACE
environment variable.
```

And above all, measured on 1.15.4: if it names a workspace that does **not**
exist, a plain command **creates** it. A `TF_WORKSPACE=prd terraform apply` does
not complain, it builds a ghost environment and applies into it.

## Two options that save time

```bash
terraform workspace select -or-create recette
terraform workspace new -state=ancien.tfstate reprise
```

The first avoids testing for existence before switching. The second seeds a
workspace **from an existing state**, the escape hatch when splitting a project.
Mind its message, which announces "You're now on a new, empty workspace" even
though the imported state is very much there.

## Your turn

```bash
dsoxlab run environments-workspace
dsoxlab check environments-workspace
dsoxlab hint environments-workspace
```

It runs **offline**, on the `local` and `random` providers.

Exam sub-objective covered: **3c**.

Reference: [Terraform workspaces](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/workspace/)
