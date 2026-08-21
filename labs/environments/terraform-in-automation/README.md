# A CI decides on exit codes

A pipeline has no keyboard and does not read coloured output. All it can do is
read an **exit code**. This lab has you build the chain, then **record** what
Terraform actually answers.

## The three outcomes of a plan

Without options, `terraform plan` returns **0** both when there is nothing to do
and when changes remain: no decision is possible. **`-detailed-exitcode`**
separates the three cases, and all three were measured:

| Code | When |
| --- | --- |
| **0** | no change, after the apply |
| **1** | error, on a broken configuration |
| **2** | pending changes, before the apply |

## Never wait for input

A command waiting for input in CI does not fail: it **occupies** an agent until
the job times out. With `-input=false`, waiting becomes an immediate failure.
Measured, on a root variable with no value:

```text
Error: No value for required variable
```

Exit code **1**, in **0.04 second**. The command does not wait.

## `fmt -check` does not return 1

It returns **3**. A pipeline testing `-eq 1` therefore lets a badly formatted
repository through without ever flagging it, and one that omits `-recursive`
looks at a single directory.

## What a saved plan freezes, and what it does not

This is the most counter-intuitive part. The plan freezes **variable values**:
changing them at apply time is **refused**.

```text
Error: Can't change variable when applying a saved plan
```

But **planning modes** are **accepted and ignored**, silently. Measured, each
option against a **fresh** creation plan:

| Option | Result |
| --- | --- |
| `-var` | **error**, exit 1 |
| `-destroy` | **accepted**, and the resources are **created** |
| `-refresh=false` | accepted, no effect |
| `-target=...` | accepted, no effect |

In other words, `terraform apply -destroy tfplan` on a creation plan **creates**,
returning 0. A script that believes it is destroying is building.

## The lock

Two concurrent runs against the same state is daily life in CI. Measured, a
`plan` launched while an `apply` holds the lock:

```text
Error: Error acquiring the state lock
```

Exit **1**, in **0.0 second**: the `-lock-timeout` default is **0s**. With a long
enough delay, the same command waits and returns **0**.

## The leak

The plan file looks opaque, since it is compressed. Reading it back as JSON still
yields the secret **in clear**, including for a variable marked `sensitive`:

```bash
terraform show -json tfplan | jq -r '.variables.mot_de_passe.value'
```

And its default name, `tfplan`, has **no extension**: a `.gitignore` that only
knows `*.tfplan` will not catch it.

## Your turn

```bash
dsoxlab run environments-terraform-in-automation
dsoxlab check environments-terraform-in-automation
dsoxlab hint environments-terraform-in-automation
```

It runs **offline**. Expect about a minute: the apply must last long enough for a
lock to be **observable**.

Exam sub-objective covered: **3c**.

Reference: [running Terraform in automation](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/terraform-en-automation/)
