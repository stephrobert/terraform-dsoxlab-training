# The summary of a run says what was planned, not what happened

The Professional's objective 6 is assessed **by multiple choice** and needs no
account. But what a CLI receives from a remote run is not a mystery: it is the
structured stream `terraform apply -json` produces locally, one JSON message per
line, which is what lets HCP Terraform display a run as it goes instead of at the
end.

This lab records a real one, from a run that **fails midway**, and reads it.

## One message type per moment of the run

| Type | What it says |
| --- | --- |
| `version` | Terraform's version, once, at the start |
| `planned_change` | one per resource the plan intends to change |
| `change_summary` | the counts, per operation |
| `apply_start` | an application begins |
| `apply_complete` | an application **completed** |
| `apply_errored` | an application **failed** |
| `diagnostic` | the error's detail, with the offending address |

## The measurement this lab is built on

Measured on 2026-09-25 with Terraform 1.16.1, on the same configuration depending
on whether it completes:

| Run | `change_summary` messages |
| --- | --- |
| completes | two, `operation: plan` then `operation: apply` |
| fails midway | **one**, `operation: plan` alone |

So on an interrupted run, the only summary in the stream is the one the plan
**announced**:

```json
{"type":"change_summary","changes":{"add":3,"change":0,"remove":0,"operation":"plan"}}
```

It says three additions. Two resources were created. Nothing in that message
says so, and the difference is only readable by counting the `apply_complete`
messages.

That is why filtering on `operation == "apply"` — the right reflex on a run that
completes — returns nothing here.

## Reading a JSONL stream in HCL

A JSONL file is not JSON: it is one object per line. It gets split, then decoded,
and the guard comes **before** the decode, because `jsondecode("")` fails:

```hcl
locals {
  messages = [
    for ligne in split("\n", file("${path.module}/../flux/run.jsonl")) :
    jsondecode(ligne) if trimspace(ligne) != ""
  ]
}
```

From there, `distinct` avoids writing the list of types by hand: it is read from
the stream, so a richer stream counts without changing anything.

## Three workflows, and what each one forbids

| Workflow | What it does | What it forbids |
| --- | --- | --- |
| **UI/VCS** | the repository is the source of truth | **no remote apply from the CLI** |
| **CLI** | uploads an archive of the local directory | needs console input to approve |
| **API** | you upload the configuration version | nothing, and that is why it is recommended for CI |

Two details worth keeping. A CLI run takes its **code** from the local directory
but its **variable values** from the workspace. And `.terraformignore`, supported
since Terraform 0.12.11, excludes files from what gets uploaded.

## Over to you

```bash
dsoxlab run hcp-terraform-remote-runs
dsoxlab check hcp-terraform-remote-runs
dsoxlab hint hcp-terraform-remote-runs
```

Twelve tests. They re-read your stream and recompute what your analysis should
have returned: nothing is frozen, and a hand-written stream fails, because the
state of the system has to agree with it.

Exam objective targeted: **6a**.

Reference: [the CLI-driven run workflow](https://developer.hashicorp.com/terraform/cloud-docs/run/cli)
