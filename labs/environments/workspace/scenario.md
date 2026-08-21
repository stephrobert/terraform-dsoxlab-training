# Scenario: one directory, three states that never see each other

**Exam sub-objective covered: 3c (running Terraform in automation).**

A workspace isolates state, never rights nor the backend. This lab covers the two
traps guides forget: `TF_WORKSPACE` blocks `workspace select` and
`workspace new` while it is set, and `workspace delete -force` removes the record
of the resources without removing the resources.

## Target capability

Drive several state instances inside a single working directory without ever
duplicating the configuration: derive naming and sizing from
`terraform.workspace`, select a workspace non-interactively, and retire an
obsolete workspace without leaving an orphan behind.

## Where the learner starts

`challenge/work` is already initialised, with the `local` and `random` providers
locked by `.terraform.lock.hcl`, and contains:

- `main.tf`: a `random_pet` and a `local_file` written three-quarters of the way,
  where the produced file name and the instance count are stubbed with `???`, to
  be replaced by an expression based on `terraform.workspace`.
- `variables.tf`: a `nom_env` variable **with** a default value. That is the
  trap: using it passes for `dev` and fails on `prod` as well as on the witness
  workspace. The default is not a convenience: measured on 1.15.4, a root
  variable without a `default` is required **even when no expression references
  it**, which would make every learner command fail on
  `No value for required variable`.
- `outputs.tf`: three outputs already written, `workspace_actif`,
  `fichier_produit` and `replicas`, which must not be modified.
- `terraform.tfstate.d/bac-a-sable/`: an inherited workspace, already applied,
  whose file `sorties/app-bac-a-sable-0.conf` is the only content of `sorties/`.

## The state to reach

1. The directory knows exactly three workspaces: `default`, `dev` and `prod`.
   `bac-a-sable` is gone.
2. `default` tracks no managed resource: the root state stays empty.
3. `dev` tracks two managed resources and produces a single file; `prod` tracks
   four and produces three.
4. Every produced file carries the name of the workspace that created it, with no
   literal `dev` or `prod` value anywhere in the configuration.
5. Neither `dev` nor `prod` has pending changes.
6. The file `sorties/app-bac-a-sable-0.conf` no longer exists: the workspace was
   destroyed before being deleted, not deleted with `-force`.
7. The workspace selected at the end of the work is `default`.

## How it is proven

The tests open no `.tf` file. They query each workspace without touching the
learner's selection, by setting `TF_WORKSPACE` on the command:
`terraform show -json` returns resources in `mode: managed` per workspace, which
proves points 2 and 3, and `terraform output -json` returns the file name that
was actually computed. The workspace inventory comes from the subdirectories of
`terraform.tfstate.d`, written by Terraform, never from human-readable output.
Point 5 is a `terraform plan -detailed-exitcode` expected to return 0 for both
`dev` and `prod`, and point 7 is read from `.terraform/environment`.

Point 6 is an absence on disk: a `-force` would have left the inherited file in
place, for lack of a destroy. The state of the system separates the two gestures
where the typed command would not.

Point 4 is the only one requiring a copy of the directory: the tests run
`terraform workspace select -or-create controle` there, then an apply, and expect
a file named after `controle` with a single instance. A hard-coded value, or a
`nom_env` pinned by a `.tfvars`, produces the wrong name here and fails.

**Note on replaying the reference solution.** `scripts/verify-solutions.py`
re-copies every fixture before laying the solution on top, and it cannot delete:
the inherited workspace and its file always come back. The two checks that prove
a **removal** (points 1 and 6) therefore abstain explicitly in that mode, with a
message saying so. They are played in full on the learner path.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/workspace/
