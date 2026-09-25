# Scenario: one word, two meanings, two attachment strategies

**Exam objective targeted: 6b, HCP Terraform workspaces and their configuration options.**

Objective 6 is assessed by multiple choice: no HCP Terraform account, no remote run. This
lab therefore needs **no account and no `terraform login`**, and it still proves something
real, because a `cloud` block is checked long before any authentication.

Two teams share a repository. One attaches its directory to a single named workspace, the
other selects a whole set of them by tags. Neither configuration initializes, and
`terraform validate` says both are fine.

## Capability targeted

Tell apart the two things the word *workspace* names, attach a directory to HCP Terraform
by the right strategy, and know where a `cloud` block is checked, which decides what
`validate` can and cannot tell you.

## Where the learner starts

`challenge/work` holds three directories:

1. `nomme/`, which must attach **by name** to the `app-prod` workspace of the
   `atelier-dsoxlab` organization. It carries three faults, and they are not caught in the
   same place.
2. `etiquete/`, which must attach **by tags**, with a `project` and no `name`. It carries
   two faults of another kind.
3. `questionnaire/`, five answers to place in `reponses.auto.tfvars`. The type is supplied
   and validated: an answer outside the enumeration is refused **at plan time**, with a
   message saying what to write.

## The state to reach

1. `nomme/` attaches by name, with `organization` as a **string literal**: a `cloud` block
   is resolved before any expression is evaluated, so it can reference no named value, not
   even a variable with a default.
2. `nomme/` no longer carries a `backend` block: a `cloud` block **is** the backend, and
   the two cannot coexist.
3. `nomme/` no longer carries `tags` next to `name`: these are two attachment strategies
   and they exclude one another.
4. `etiquete/` declares a single `cloud` block, with `project` and `tags`, and no `name`.
5. The five answers say what a CLI workspace creates (a state), what an HCP workspace is
   (a unit of execution), where a run's input variables live (the workspace), why `name`
   and `tags` exclude one another (two strategies), and what `validate` catches of the
   three faults in `nomme/` (the backend conflict alone).

## How it is proven

The two repaired directories are initialized, and the tests require the initialization to
stop **at the token** and nowhere else. That is the lab's assumed boundary: a correct
`cloud` block goes as far as `Required token could not be found`, which no faulty
configuration reaches.

That single marker would not be enough, and the measurement says why. On 2026-09-25, with
Terraform 1.16.1, a configuration holding both a `backend` and a `cloud` block, and one
holding two `cloud` blocks, **also** print `Required token could not be found`, next to
their fault. The tests therefore require both: the token message present, and none of the
fault messages. Each fault message was captured from a minimal case rather than assumed.

The tests also neutralize any token on the machine, an empty CLI configuration file and no
`TF_TOKEN_*` variable, because the same correct configuration answers `Failed to read
organization` on a machine that has run `terraform login`. Without that, a learner who uses
HCP Terraform elsewhere would be failed for correct work.

The questionnaire is read from `terraform output -json`, never from the file.
