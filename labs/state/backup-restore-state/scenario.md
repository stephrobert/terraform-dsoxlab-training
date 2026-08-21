# Scenario: restore an amputated state without recreating the infrastructure

**Target exam sub-objective: 1e, manage state, import resources and reconcile drift.**

A state manipulation went wrong, the safety nets are gone, and three candidate
backups remain of which only one is restorable. The trap addressed here is the
guard rail itself: `lineage` and `serial` decide whether a restore repairs the
infrastructure or has it recreated.

## Target capability

Pick the right state backup among several candidates by comparing `lineage` and
`serial`, push it back with `terraform state push` despite Terraform's refusal,
and prove the existing infrastructure was never touched. The capability includes
the prior reflex: photograph the damaged state before writing into it, because a
`push` cannot be replayed.

## Where the learner starts

The lab is a `shell` one: no virtual machine, no `dsoxlab provision`, everything
happens in `challenge/work` with the `hashicorp/local` provider alone.

The directory holds a complete, already applied configuration: three `local_file`
resources that wrote three files under `artefacts/`. Nothing is holed in the
code, there is no `???` to fill in. All the work is on the state, not the HCL.

The incident already happened. The `terraform.tfstate` present describes only two
of the three resources: the third was removed by a careless `terraform state rm`,
which bumped the `serial`. The files under `artefacts/` are intact on disk: it is
the state that lies, not the infrastructure.

The safety net is gone, and that is one of the lab's lessons. A state
manipulation command does **not** write into `terraform.tfstate.backup`: it drops
a **timestamped** `terraform.tfstate.<epoch>.backup` file, verified on 1.15.4.
Here a directory cleanup took away every `*.backup` file, which most repositories
gitignore. All that remains is the amputated state and the three candidates under
`sauvegardes/`.

A `sauvegardes/` directory provides three JSON files, with no hint of their
provenance:

- one is complete, carries the right `lineage` and matches the disk;
- one carries the right `lineage` but predates the last apply, with stale content
  for one of the files;
- one looks complete but comes from another project, its `lineage` is foreign.

## The state to reach

1. A `sauvegardes/avant-restauration.json` file exists, produced by
   `terraform state pull` before any write: a valid photo of the damaged state,
   with the project `lineage` and only two resources in `mode: managed`.
2. The current state carries the project's original `lineage`. The foreign-lineage
   backup was therefore not pushed, not even by force.
3. The current state describes the three `local_file` resources again, at the same
   addresses as before the incident.
4. The current state `serial` is strictly greater than the restored backup's,
   which attests to a real `push` and not a file copied by hand over
   `terraform.tfstate`.
5. The configuration has converged: no change pending.
6. The three files under `artefacts/` keep the same content and the same
   modification time as at the start. Nothing was destroyed or recreated.

## How it is proven

Validation never opens a `.tf` file and never reads human-facing output. It
queries structured state:

- `terraform state pull` is read as JSON for points 2 and 4: `lineage` compared
  with the reference frozen in `reference/etat-initial.json`, and `serial`
  compared with the restorable backup's. An equal `serial` betrays a file copy, a
  different `lineage` betrays the wrong backup.
- The same document gives point 3: the managed resources are counted and their
  addresses compared with the three expected ones.
- `sauvegardes/avant-restauration.json` is parsed as a state: `lineage`, and a
  count of two managed resources. A file that is empty, truncated or taken after
  the restore fails.
- `terraform plan -detailed-exitcode` must return 0 for point 5. That test is what
  eliminates the stale backup: restoring it leaves a gap between the state and the
  real content of one file, and the exit code is then 2.
- Content and modification time of the three files under `artefacts/` are compared
  with the reference laid down by the fixtures. A recreation, even with identical
  content, rewrites the file and moves its modification time, which fails the test.
  This is what rules out the `terraform apply` shortcut, which recreates the object
  missing from the state instead of repairing the state.
- A behaviour check, played in a temporary copy: pushing the foreign-lineage backup
  must fail on `over unrelated state`. It does not grade the learner's work, it
  verifies the guard rail still exists.

A `challenge/work` left as is passes none of these proofs: without a restore,
`terraform state pull` returns only two resources and the plan exits with code 2.
