# Scenario: Pro, integrative mock exam

**Exam objectives targeted: all six**, under the conditions of the real sitting.

The Terraform Authoring and Operations Professional exam lasts **four hours** and
mixes multiple-choice questions with hands-on work: writing code, diagnosing,
repairing. The Terraform documentation and the provider documentation are
available during the exam.

## Capability targeted

Chain, within the allotted time and unaided, six tasks covering the six
objectives. This is not a learning lab: it is a dress rehearsal, to be played
once the six capstones are done, and in one sitting.

## Where the learner starts

`challenge/work` holds six directories, one per task, each deliberately
imperfect. Files already laid down outside Terraform, a configuration that does
not validate, three copies of one pair of resources, two root modules that
ignore each other, a missing provider configuration, and twelve unanswered
questions.

The lab runs **offline**, on the `local` and `random` providers: no VM, no
account, no emulator. That is a choice, and it has a price, stated below.

## The state to reach

1. **Objective 1**: adopt a file corrected by hand without overwriting that
   correction, and reach a stable plan.
2. **Objective 2**: fix three faults that `validate` names, replace three
   resources with a single one driven by `for_each`, and make the plan refuse a
   port outside the allowed range.
3. **Objective 3**: publish a contract as outputs from one root module, consume
   it from the other, with nothing hard-coded.
4. **Objective 4**: factor three environments into a local module, with no
   resource destroyed or recreated.
5. **Objective 5**: attach a resource explicitly to a second provider
   configuration, set the permissions in the right place, and write a version
   constraint that brackets the series.
6. **Objective 6**: answer the twelve HCP Terraform questions, against a global
   threshold and a coverage requirement on the four sub-objectives.

## How it is proven

- **One test section per task**, independent of the others: a failed task does
  not fail the following ones, and the score says which objective to revisit.
- The proofs are read from state: `terraform show -json`, the state file, the
  lock file, the real permissions on disk.
- Three tasks require a **stable** plan afterwards, which rules out succeeding
  through a detour that rebuilds on every run.

## What this mock does not cover, and why

Local providers cannot import: `local` and `null` both answer
`Resource Import Not Implemented`. Import is therefore proven elsewhere, by
`capstone1-resource-lifecycle` and `aws-import-moved-drift`, which have a real
provider. Here, task 1 proves the other half of the same sub-objective, drift
reconciliation.

For the same reason, objective 5 is proven on attachment and version
constraints, not on authenticating a remote provider.
