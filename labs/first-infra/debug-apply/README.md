# Resume after a failed apply, without redoing the work

A `terraform apply` that stops midway does not leave a mess: it leaves a
**partial and coherent state**. Terraform is designed to resume where it
stopped, and yet the first reflex is almost always to destroy everything and
start over.

In this lab that costs a few seconds. On a database it costs the data.

## State does not say what you think

Here is the fact this lab exists to have you observe. After a failure, the
offending resource **is not absent** from state. It is there, marked `tainted`:

```console
$ terraform show -json | jq '.values.root_module.resources[] | {address, tainted}'
{"address": "random_pet.identifiant", "tainted": null}
{"address": "local_file.inventaire",  "tainted": null}
{"address": "null_resource.rapport",  "tainted": true}
```

`tainted` means: "this object was created, something failed afterwards, I do not
know what state it is in, I will **replace** it on the next apply".

That is a nuance people rarely read, and it changes everything. You are not
facing two created resources and a missing one, but two **healthy** resources
and one **to resume**.

## Fix the cause, and nothing else

The goal is to repair **the cause**. Four reflexes come first, and all are wrong:

| Reflex | Why it is wrong |
| --- | --- |
| delete the offending resource | the failure goes away, so does the requirement |
| comment it out | same, with a memento in the repository |
| `mkdir` by hand | the configuration stays wrong, it will fail elsewhere |
| `destroy` then redo everything | destroys two healthy resources to repair one |

The third is the most interesting, because it **works**. The apply passes, the
plan converges, and everything is green on the machine of whoever typed the
command. That is exactly why the lab's last test replays the configuration in a
**clean** directory: a fix that lives only in its author's shell is not a fix.

## The resumption fingerprint

How do you prove you **resumed** rather than **redid**? The final state is the
same either way. What tells them apart are the identifiers:

```console
$ terraform show -json | jq -r '.values.root_module.resources[]
    | "\(.address) \(.values.id)"'
```

A resumed resource keeps its id. A recreated one receives a different one. The
lab records those from the supplied state, then compares them after the repair:
any difference signs a destruction followed by a recreation.

## Where to look when the cause is not obvious

The error message says *that* it failed, rarely *why*. Two tools beat rereading
the code:

```bash
terraform plan -json | jq 'select(.@level == "error")'
```

```bash
TF_LOG=DEBUG TF_LOG_PATH=/tmp/tf-debug.log terraform apply
```

`TF_LOG_PATH` matters as much as `TF_LOG`: without it the trace goes to the
terminal, mixes with normal output and scrolls away. With it, it sits in a file
you can read once things have calmed down.

## Over to you

```bash
dsoxlab run first-infra-debug-apply
dsoxlab check first-infra-debug-apply
dsoxlab hint first-infra-debug-apply
```

The lab runs **offline**, on the `random`, `local` and `null` providers: the
failure is deterministic and reproduces identically on any machine. The partial
state is **supplied**: you arrive as one arrives on an incident, facing a state
you did not produce.

Exam objective targeted: **1e**, supported by **1c**.

Reference: [debugging an apply](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/debug-apply/)
