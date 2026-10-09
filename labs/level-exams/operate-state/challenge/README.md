# Level B exam: take over the operation of a platform

You take over the operation of a platform already in service: two libvirt
machines, `web` and `db`, described in `plateforme/`, whose state lives in the
team's shared S3 store. The team's identity on that store is in `exam.env`, and
the team left in `sauvegardes/` the copy of the state taken last night.

Last night, **an incident** hit the operation. Nobody knows which one: finding
out is part of the work.

Indicative duration: **90 minutes**. No hint is offered.

## What is expected

Three results, checked on the real state of the machines, the store and the
plans, never on the shape of your code:

- **Production is put back on its feet without any machine being recreated.**
  The machines keep their identity, they run, and the production plan proposes
  nothing anymore.
- **`dev` and `prod` are separated.** A `dev` environment exists, with its own
  `web` and `db` machines (prefix `<prefix>-dev-` instead of `<prefix>-prod-`),
  and a mistake on one can never touch the other. The file layout is free.
- **The delivery chain runs without a human.** Ship at the root of your working
  directory an executable `chaine.sh` script, which the harness will call this
  way:

  ```text
  ./chaine.sh <env> plan     # 0: nothing to do · 2: changes to apply · 1: error
  ./chaine.sh <env> apply    # applies the plan produced by the last "plan" of that env
  ```

  The script never asks a question, applies only the plan that was produced and
  therefore reviewed, and leaves no plan file behind.

## The operating rules

The team holds to four rules, which the harness will check:

1. When another run holds the state lock, your chain **waits** for it to be
   released; it does not fail at once and never forces it.
2. A **backup** of the state exists before every write it causes.
3. Nothing recreates a machine to "repair" the state.
4. The two environments share **no** state.

## How it is graded

The report gives a verdict per skill: `state`, `refactor`, `environment`,
`automate`. A failing skill points to the lessons that teach it.

To get graded: `dsoxlab check`.
