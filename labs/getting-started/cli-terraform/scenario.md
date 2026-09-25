# Scenario: the Terraform CLI as an automation tool

**Exam objective targeted: 3c, run the Terraform workflow in automation.**

A lab checking that commands were typed would prove nothing. What can be proven
is that a non-interactive chain goes through the configuration without a human
having to read a single output formatted for them.

## Capability targeted

Drive Terraform from a script: obtain a verdict from an exit code, use machine
output (`-json`) rather than displayed text, and evaluate an HCL expression
without opening an interactive session.

## Where the learner starts

`challenge/work` holds a configuration resting solely on the `local`, `null` and
`random` providers: no cloud, no VM, no cost. The directory is bare, with no
`.terraform/`, no lock file and no state.

Three defects are placed deliberately: a `.tf` file outside canonical format
which makes `terraform fmt -check` exit non-zero, an error making
`terraform validate` fail (`valid` at `false`, `error_count` above zero), and
missing outputs although they are the only channel through which the
configuration exposes its values to a script. Everything must run without
interactive confirmation.

## The state to reach

1. The directory is initialised and the lock file exists. Without that step,
   `validate` fails for a reason unrelated to code quality.
2. No file is outside canonical format any more.
3. The configuration is valid, with no diagnostic of severity `error`.
4. The configuration is applied without interaction, and state holds exactly the
   expected resource addresses.
5. The requested outputs exist and carry the values the configuration computes,
   among them a value coming from an expression that must be recomputable
   outside state.
6. Replaying a plan after the apply announces no change.

## How it is proven

No test reads back the learner's `.tf`, and none parses human output. Everything
goes through exit codes and JSON:

- `terraform fmt -check -recursive` must exit 0. A non-zero code proves a file
  remains outside canonical format: that is the contract the official
  documentation announces.
- `terraform validate -json` is parsed: `valid` is `true` and `error_count` is
  `0`.
- `terraform output -json` is parsed: the expected keys are present and their
  values match what the configuration must produce.
- `terraform state list` lists exactly the expected addresses, and
  `terraform show -json` confirms their presence in state.
- An expression is evaluated non-interactively, by passing it on the standard
  input of `terraform console`, and the result is compared to the expected value.
- `terraform plan -detailed-exitcode` exits 0, meaning success with no change. A
  2 would signal drift, a 1 an error.
