# 🎯 Challenge: three backups, only one restorable

## 📦 Starting point

`challenge/work` holds a project that was **already applied**, and an incident
that already happened. Nothing is holed: **no `???`, no `.tf` to edit**. All the
work is on the state.

```bash
terraform init
terraform state list
```

The state describes only **two** resources, while `main.tf` declares **three**
and the **three files** under `artefacts/` are right there. A careless
`terraform state rm` went through.

| File | What it is |
| --- | --- |
| `main.tf` | the configuration, complete, **do not touch** |
| `artefacts/*.txt` | the three real objects, **intact** |
| `terraform.tfstate` | the amputated state, the one that lies |
| `reference/etat-initial.json` | frozen copy of that state, **do not modify** |
| `sauvegardes/sauvegarde-{1,2,3}.json` | three candidates, unlabelled |

**There is no safety net.** A state manipulation command does not refresh
`terraform.tfstate.backup`: it drops a timestamped
`terraform.tfstate.<epoch>.backup` file, and a directory cleanup took them all
away. What is left fits in `sauvegardes/`.

## ✅ Objective

Bring the state back in line with the infrastructure, **without any of the three
artefacts being recreated**. Only one of the three backups allows it.

## 📋 What you must obtain

1. A `sauvegardes/avant-restauration.json` file, produced **before any write**,
   holding the damaged state as is: the project `lineage` and its **two**
   managed resources.
2. The current state still carries the project's original `lineage`.
3. The current state describes the **three** `local_file` resources again.
4. The current state `serial` is **strictly greater** than the restored backup's.
5. `terraform plan -detailed-exitcode` exits with **code 0**.
6. The three files under `artefacts/` keep their original content **and
   modification time**: none was rewritten.

## ⚠️ The heart of the matter

Two fields tell the three candidates apart, and a third trap waits at the end:

| Field | What it says | What it rules out |
| --- | --- | --- |
| `lineage` | the identity of the state line | a backup from **another project** |
| `serial` | the write counter | a **stale** backup, older than the last apply |

Terraform refuses a `push` with an older `serial` straight away: that is normal,
a restore necessarily puts an earlier state back. `-force` overrides it,
**without confirmation, and without rechecking the lineage**. Checking it is on
you.

The shortcut that seems to work, `terraform apply`, repairs nothing: it
**recreates** the object missing from the state instead of repairing the state,
and the tests compare modification times.

## 🔍 Validation

`dsoxlab check state-backup-restore-state` proves, by execution:

- the prior photo exists and describes the **damaged** state;
- the current state `lineage` is the project's, so the foreign backup was not
  pushed;
- the three resources are managed again;
- the current `serial` is greater than the backup's, which a `push` produces and
  a file copy does not;
- the plan proposes nothing, which rules out the stale backup;
- the three artefacts were neither deleted nor rewritten;
- behaviour check played in a copy: pushing the foreign backup does fail on
  `over unrelated state`.

Stuck? `dsoxlab hint state-backup-restore-state`.
