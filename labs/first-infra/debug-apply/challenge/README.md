# 🎯 Challenge: resume after a failed apply

## Starting point

`challenge/work` holds a configuration that **already failed**, and its state is
provided. No cloud, no VM, no network access: the failure is **deterministic**
and reproduces identically on any machine.

Look at the state before touching anything:

```bash
terraform show -json | jq '.values.root_module.resources[] | {address, tainted}'
```

## 🧭 What the state actually says

The failing resource is **not absent** from the state. It is there, marked
`tainted`: Terraform knows it is in a doubtful state and will **replace** it on
the next apply. That nuance is rarely read, and it changes how you resume.

Two resources out of three are **perfectly healthy**. The reflex of destroying
everything to start over is exactly what this lab wants you to lose.

## ✅ Objective

Fix **the cause** in the configuration.

What not to do, and what comes to mind first:

| Reflex | Why it is wrong |
|---|---|
| delete the failing resource | the failure goes away, so does the need |
| comment it out | same, with a memory in the repository |
| `mkdir` by hand | the configuration stays wrong: it will fail elsewhere |
| `terraform destroy` then redo | destroys two healthy resources to fix one |

## 🔍 Validation

```bash
dsoxlab check first-infra-debug-apply
```

Five tests. The heart of the lab is the **resume fingerprint**: the identifiers
of the already created resources are compared to those of the provided state.
Any different value signals a destroy followed by a recreate — the final state
would be correct, but the work would have been **redone** instead of resumed. On
a local file that costs nothing; on a database, it costs the data.

The last test replays your configuration in an **empty** directory. A `mkdir`
run by hand makes the apply pass on your machine and nowhere else.
