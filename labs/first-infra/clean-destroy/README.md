# Destroying cleanly, and the four things it covers

"Destroy" names four operations that are not alike. Confusing them leads to two
symmetric mistakes: believing a guard rail protects when it no longer does, and
deleting a file you needed to keep.

The lab runs **offline**, on the `random`, `local` and `null` providers:
everything is deterministic and replayable.

## The four gestures

| Gesture | What it does |
| --- | --- |
| full `destroy` | everything, except what a guard rail **refuses** |
| `destroy -target` | **only** what you name |
| removing from code | destroyed on the next `apply`, with **no `destroy` at all** |
| complete `destroy` | empties state, **without deleting its file** |

The third is the one you suffer without asking for it. Deleting a resource block
is not neutral: on the next `apply`, Terraform sees the object exists and is no
longer declared, and destroys it. That is the normal mechanism, and it is also
how a resource gets lost while tidying a file.

## `prevent_destroy` refuses to plan

```hcl
resource "local_file" "inventaire" {
  # ...
  lifecycle {
    prevent_destroy = true
  }
}
```

It is not a lock on the object, it is a **refusal to plan**. It applies to any
plan that would take the resource with it, including a full `destroy` launched
without thinking.

Two limits worth knowing, and the second surprises people:

- it protects nothing once the **block leaves the configuration**. The guard rail
  lives in the code; removing the code removes the guard rail;
- **a plan that fails writes its file anyway.** Measured while writing this lab:
  `terraform plan -destroy` on a protected configuration exits with **code 1**
  and produces the file requested by `-out` all the same. That plan is
  **incomplete**, three resources out of four, the protected resource dragging
  its dependencies out of the plan.

A plan file that exists although the command failed is exactly the kind of thing
nobody distrusts. You read it back, you believe it, and it lies by omission.

## A destruction plan can be read before it runs

```bash
terraform plan -destroy -out=destroy.tfplan
terraform show -json destroy.tfplan | jq '[.resource_changes[].address]'
```

That is the only way to know what a `destroy` will take **before** it takes it.
On a real configuration the list often holds surprises: resources created by a
module, or depending on the one you aimed at.

## State empties, its file stays

This is the trap at the end of the lab, and it costs dearly outside the lab:

```console
$ terraform destroy -auto-approve
$ terraform show -json | jq '.values.root_module.resources'
null
$ ls terraform.tfstate
terraform.tfstate
```

The file is still there, and it **must** be. It carries the project's `lineage`
and its `serial`. Deleting it "to be tidy" makes Terraform start from zero: it
loses the link with anything that survived, and no longer knows it has already
managed those objects.

Emptying state and deleting its file are two different things. The lab checks
both separately, deliberately.

## Over to you

```bash
dsoxlab run first-infra-clean-destroy
dsoxlab check first-infra-clean-destroy
dsoxlab hint first-infra-clean-destroy
```

Five tests. The guard rail is judged on the **exit code** rather than the
message, because text changes between versions. The destruction plan is judged
on the **number of addresses**, because a test checking only the file's existence
would pass on a mutilated plan.

Exam objective targeted: **1d**, supported by **1e**.

Reference: [destroying cleanly](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/destroy-propre/)
