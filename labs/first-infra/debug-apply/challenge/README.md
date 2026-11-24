# Resuming an apply interrupted halfway

## The situation

**Exam objective targeted: 1e (interpret and manipulate state after a partial apply), supported by 1c (run `terraform apply`).**

A `terraform apply` stops on an error after creating part of the resources. State
is neither empty nor complete: it is partial, and yet coherent.

## Capability targeted

Diagnose an `apply` that fails midway, fix the cause, then converge on the target
state **without starting over**. This is the gesture separating the beginner from
the professional: the natural reflex is to destroy everything and begin again,
whereas Terraform is designed to resume where it stopped. Destroying what
succeeded costs time in a lab, and data in production.

The capability breaks down into three moments:

1. **Observe** that the failure is partial, by reading state rather than the
   error message.
2. **Locate** the offending resource, with `terraform plan -json`, or `TF_LOG=DEBUG`
   together with `TF_LOG_PATH` to isolate the logs in a file.
3. **Repair then converge**, checking that resources already created are neither
   destroyed nor recreated.

## Where the learner starts

The `challenge/work` directory holds a Terraform configuration using only local
providers (`random`, `local`, `null`): no VM, no cloud, no network access. The
failure is therefore **deterministic** and reproduces identically on any machine.
The configuration describes a short chain of resources: a random identifier, a
file generated from it, then a local-exec resource depending on both. That last
one fails deliberately, because it writes into a directory nothing creates.

**The partial state is supplied**, so the learner does not have to trigger the
failure: they arrive as one arrives on an incident, facing a state they did not
produce.

That state holds a surprise the lab exists to have you observe: the offending
resource **is not absent**. It appears in state, marked `tainted`. Terraform
knows it is in a doubtful state and will **replace** it on the next apply. That
is the first thing to look at, and it changes how you resume:

```bash
terraform show -json | jq '.values.root_module.resources[] | {address, tainted}'
```

## The state to reach

- The cause of the failure is fixed in the configuration, without deleting the
  offending resource or neutralising it by commenting it out.
- The offending resource is no longer marked `tainted`: it completed.
- Every declared resource is present in state.
- Resources created before the failure carry **the same identifiers** as before
  the repair: they were neither destroyed nor replaced.
- The working directory has converged: a new `plan` proposes nothing.
- The configuration replays **on a clean directory**.

## How it is proven

Through structured state and exit codes, never through the learner's code nor the
text of an error message.

- **The taint is gone**: the originally offending resource appears in state
  without `tainted`. That is proof it completed, not that it was made to
  disappear.
- **The resource still exists**: deleting it from the configuration would also
  make the failure disappear, and that is the most tempting wrong answer.
- **Resumption fingerprint**: the identifiers of already created resources are
  recorded from the supplied state, then compared after the repair. Any
  difference signs a destruction followed by a recreation, hence a failure.
- **Real effect**: the file produced by the originally offending resource exists
  on disk, which proves the repair actually let the execution complete.
- **Convergence, and a clean replay**: `terraform plan -detailed-exitcode` exits
  **0**, and the configuration is replayed in a **clean** directory. A `mkdir`
  run by hand would make the apply pass on the learner's machine and nowhere
  else.

## 🎯 Challenge: resume after a failed apply

### Starting point

`challenge/work` holds a configuration that **already failed**, and its state is
provided. No cloud, no VM, no network access: the failure is **deterministic**
and reproduces identically on any machine.

Look at the state before touching anything:

```bash
terraform show -json | jq '.values.root_module.resources[] | {address, tainted}'
```

### 🧭 What the state actually says

The failing resource is **not absent** from the state. It is there, marked
`tainted`: Terraform knows it is in a doubtful state and will **replace** it on
the next apply. That nuance is rarely read, and it changes how you resume.

Two resources out of three are **perfectly healthy**. The reflex of destroying
everything to start over is exactly what this lab wants you to lose.

### ✅ Objective

Fix **the cause** in the configuration.

What not to do, and what comes to mind first:

| Reflex | Why it is wrong |
|---|---|
| delete the failing resource | the failure goes away, so does the need |
| comment it out | same, with a memory in the repository |
| `mkdir` by hand | the configuration stays wrong: it will fail elsewhere |
| `terraform destroy` then redo | destroys two healthy resources to fix one |

### 🔍 Validation

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
