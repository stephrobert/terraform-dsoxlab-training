# The essential commands, and what they refuse to do

The Associate 004 is a **one-hour multiple-choice exam**. You type nothing, and
that is exactly the trap: revising a table of commands feels like knowing them,
right up to the question about what a command **refuses** to do, or the code it
returns when it fails.

This lab does not revise that table. It has you **record six exit codes** on a
handful of files that fit in one directory, and every one of them contradicts a
formula people recite without ever having checked it.

## `validate` is not a spell checker

The saying is "`validate` only checks syntax". It is wrong on both counts.

**It does less than people think**: it needs the providers' **schemas**, so it
can validate nothing before `init`. Run on a fresh directory it exits **1**,
not because the configuration is bad, but because it has nothing to judge with.

```console
$ terraform validate
╷
│ Error: Missing required provider
...
$ echo $?
1
```

**And it does more**: once the schemas are in place it catches an attribute
that none of them defines. That is not syntax, that is meaning.

```hcl
resource "null_resource" "sonde" {
  attribut_qui_n_existe_dans_aucun_schema = true
}
```

```console
$ terraform validate
│ Error: Unsupported argument
$ echo $?
1
```

What it still does not do: reach a provider, read state, or tell you whether
your infrastructure exists. That takes `plan`.

## `fmt -check` returns 3, and it costs you in CI

This is the most useful fact in this lab, and the least known. A file outside
canonical format makes `fmt -check` exit **3**, not 1.

```console
$ terraform fmt -check -recursive ; echo $?
versions.tf
3
```

So a CI check written this way measures nothing:

```bash
terraform fmt -check -recursive
if [ $? -eq 1 ]; then
  echo "unformatted"   # never fires: the code is 3
fi
```

The correct form does not test a particular code, it tests **zero**:

```bash
terraform fmt -check -recursive
```

and lets the non-zero code fail the step.

## `plan -detailed-exitcode` has three answers, not two

| Code | What it says |
| --- | --- |
| **0** | nothing to do, infrastructure matches the configuration |
| **1** | the command failed |
| **2** | the plan succeeded, and it contains changes |

This is the only way to tell "it worked, nothing to do" from "it worked, there
is work", without reading a message meant for a human. A script testing only
`!= 0` treats drift as a breakdown.

## The precedence cascade, in order

When several sources set the same variable, the **last one loaded** wins:

1. the variable's `default`, when nobody else speaks;
2. the `TF_VAR_<name>` environment variable;
3. `terraform.tfvars`;
4. `terraform.tfvars.json`;
5. the `*.auto.tfvars` files, in alphabetical order;
6. `-var` and `-var-file`, in command-line order.

Remembering the list is not enough: this lab sets **every variable from several
sources at once**, and asks for four outputs naming which one won. That is
where you find out an environment variable loses to a plain `terraform.tfvars`,
which intuition often gets backwards.

## Rename, adopt, release: three blocks that are not alike

**`moved`** renames a resource in state without destroying anything. Writing it
is not enough: until it is **applied**, the old address stays.

```hcl
moved {
  from = random_pet.ancien_nom
  to   = random_pet.nouveau_nom
}
```

**`import`** brings an object that already existed under management. This lab's
test does not look at the address but at the **id**: a resource that was created
rather than imported carries a different one, and that is the only proof that
holds.

```hcl
import {
  to = terraform_data.provisionne_ailleurs
  id = "identifiant-connu"
}
```

**`removed`** drops a resource from state, and this is where the most expensive
trap of the set lives:

```hcl
removed {
  from = local_file.adopte

  lifecycle {
    destroy = false   # without this line, the file is DESTROYED
  }
}
```

One word between "release an object" and "delete it".

## `-replace` replaces a resource nothing required to move

`terraform plan -replace=null_resource.a_remplacer -out=plan.tfplan` produces a
plan where that address carries `["delete", "create"]`, and where **nothing
else moves**. If other resources show up in the plan, the configuration had not
converged beforehand: that is no longer a replacement, it is catch-up work.

## `sensitive` hides a display, it encrypts nothing

```console
$ terraform output
identifiant_sensible = <sensitive>
```

```console
$ jq '.outputs.identifiant_sensible' terraform.tfstate
{
  "sensitive": true,
  "value": "innocent-buck"
}
```

The value sits **in clear text in state**. Which is why the real question is
never "did I mark this output sensitive" but "where is my state stored, and who
can read it". The lab's final test demands both observations at once.

## Over to you

```bash
dsoxlab run certifications-associate-essential-commands
dsoxlab check certifications-associate-essential-commands
dsoxlab hint certifications-associate-essential-commands
```

It runs **offline**, on the `local`, `null` and `random` providers: no VM, no
cloud account.

The six codes were measured on **Terraform v1.16.1** on 2026-09-24. The tests
replay them against your configuration rather than take them on trust: should a
future version change one, the lab will be declared due for remeasurement,
rather than your work being failed.

Exam objective targeted: **3d**.

Reference: [preparing the Terraform Associate certification](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/associate/)
