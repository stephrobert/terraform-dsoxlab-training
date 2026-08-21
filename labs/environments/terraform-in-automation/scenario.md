# Scenario: a non-interactive Terraform chain, judged on its exit codes

**Exam sub-objective covered: 3c, running the Terraform workflow in automation.**

A CI has no keyboard and does not read coloured output: it decides on exit codes.
This lab has the learner build the full chain (`fmt -check`, `validate -json`,
`plan -out`, the plan read back as JSON, `apply` of the file) and shows that a
saved plan is not what most people think it is.

## Target capability

Write a fully non-interactive Terraform sequence that never blocks on a prompt,
that separates "nothing to do", "pending changes" and "error" by exit code alone,
and that applies a saved plan while knowing what that file freezes, what
sensitive data it holds, and which options become decorative once inside it. The
point is not to type `plan -out`: it is to know what an automated review gate can
legitimately conclude.

## Where the learner starts

`challenge/work` holds an incomplete `main.tf`: the `mot_de_passe` variable is
missing its marker, the `environnement` variable deliberately has no default, and
the `local-exec` command of a `terraform_data` resource is stubbed although it
must make the apply slow enough for a lock to be observable. A skeleton
`pipeline.sh` stands in for the pipeline: its five steps are `???` and it is
responsible for recording the codes it observes. The `.gitignore` is incomplete
and lets the plan file through. No `.terraform/`, no state, no `preuves/`. Shell
lab: `local`, `random` and the built-in `terraform` provider, no VM, no cloud, no
CI service.

## The state to reach

1. The configuration is formatted, valid, initialised without a prompt, applied
   from a saved plan file and converged, its apply lasting at least ten seconds.
2. `preuves/chaine.json` records the exit code of each of the five steps of
   `pipeline.sh`, none of them receiving keyboard input.
3. `preuves/codes.json` records the three values of `plan -detailed-exitcode`
   (before apply, after apply, on a broken configuration) and the code of
   `fmt -check` on a badly indented file.
4. `preuves/prompt.json` records the code and the waiting time of a
   `plan -input=false` whose root variable received no value.
5. `preuves/plan_fige.json` records the fate of four options passed to the apply
   of a saved plan: those that make the command fail, and those accepted with no
   effect.
6. `preuves/verrou.json` records the `-lock-timeout` default and the code of a
   plan launched during an apply, with that default then with a sufficient delay.
7. `preuves/fuite.json` names the exact JSON path where the sensitive value
   leaks in clear from the saved plan, and the `.gitignore` excludes that plan
   file.

## How it is proven

The tests run in `challenge/work`, open neither `main.tf` nor `pipeline.sh`, and
read no human-facing output.

- Every claim is replayed: the tests themselves re-run `fmt -check`,
  `plan -detailed-exitcode` three times, the concurrent apply and the four
  saved-plan options, then compare against the files in `preuves/`. Nothing is
  hard-coded, and the final state comes from `terraform show -json`: three
  resources in `mode: managed`.
- Three received ideas fall. The code of `fmt -check` on a badly indented file is
  not 1, it is 3. A `plan -input=false` without a variable value fails at once
  instead of waiting, measured at 0.04 second. And above all, when applying a
  saved plan, only an attempt to change a variable raises an error: planning
  modes are accepted and ignored, so an apply launched with `-destroy` on a
  creation plan creates the resources and returns 0.
- The lock is measured: with the default, the concurrent plan fails immediately
  in code 1; with a sufficient delay, it returns 0 after waiting. So is the leak:
  the plan file looks opaque, and reading it back as JSON yields the secret in
  clear at `.variables.mot_de_passe.value`.

**A precaution on the four options.** Each one is tried against a **fresh** plan
in a pristine copy. Chaining the attempts would make the plan stale, and
Terraform would answer `Saved plan is stale` without ever judging the option
itself, which is exactly what happened on the first measurement pass.

None of this passes on an empty directory, nor on an apply too fast for a lock to
be observed.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/terraform-en-automation/
