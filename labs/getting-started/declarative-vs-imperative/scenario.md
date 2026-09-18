# Scenario: prove idempotence where the imperative script diverges

**Exam sub-objective covered: 1b `plan` (prove idempotence, detect drift and fix it).**

An imperative provisioning script is provided and diverges as soon as you replay
it. The learner must reach the same result in Terraform, then show with the plan
that the second pass is a non-event.

## Target capability

Translate an intent expressed as execution steps into a configuration that
describes a target state, then establish the property separating the two
approaches: convergence. The learner must produce the machine proof of that
convergence rather than assert it, and repair an external drift without changing
their code.

## Where the learner starts

`challenge/work` contains `imperatif.sh`, a provided script that builds an output
directory, writes a report in it and records a randomly drawn identifier on every
call. Replayed, it produces a different identifier and piles its report up
instead of replacing it: the resulting state depends on the number of runs. An
incomplete Terraform configuration comes with it, with the `local`, `random` and
`null` providers and arguments to fill in, notably those deciding whether
generated values are stable. There is no `.terraform/`, no state, no lock file.
The script is to be read, not fixed.

## The state to reach

1. The project is initialised: the dependency lock file is present and the
   `local`, `random` and `null` providers are recorded in it.
2. A state exists and references three managed resources: the one fixing the
   random identifier, the one materialising the report on disk, the one whose
   trigger depends on the identifier.
3. The report file exists on disk and its content carries the identifier
   recorded in the state.
4. Two outputs are exposed: the identifier, non-empty, and the report path,
   which designates the file present.
5. Immediately after the apply, a new plan announces no action.
6. The report file is deleted outside Terraform: the plan then announces a
   single create and no replacement of the identifier.
7. After convergence, the file is back and the identifier still holds the value
   recorded before the drift.

## How it is proven

The state inventory is read with `terraform show -json`: the tests look for the
addresses of the three managed resources, the identifier and the report path.
Outputs are read with `terraform output -json`, never from the human-facing
output. The report is observed on disk then confronted with the state
attributes.

Idempotence is established with `terraform plan -detailed-exitcode`, whose exit
code must be 0 right after the apply. Drift is established the same way: after
the file is deleted, the same call must exit with 2. The plan is then saved with
`-out`, read back by `terraform show -json`, and a single create entry is
required, on the file resource and on no other.

The fix is applied without changing the code: the identifier read back by
`terraform output -json` must be identical to the one captured before the drift,
and a final `terraform plan -detailed-exitcode` must return to 0. No check reads
the content of the `.tf` files written by the learner.
