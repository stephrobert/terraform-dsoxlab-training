# 🎯 Challenge: variables, locals and the real precedence

## Starting point

`challenge/work` holds an incomplete project. **No remote provider, no VM**: the
lab runs anywhere `terraform` is on the `PATH`, without network.

`versions.tf` is already correct. `variables.tf`, `locals.tf`, `main.tf` and
`outputs.tf` are **full of holes**. `terraform.tfvars` is provided: it sets
`env` and stays **silent about `region`**.

`terraform plan` fails as is: the `???` are not valid HCL.

## ✅ Objective

1. **Four typed variables**: `env` (string, default `dev`), `replicas` (number,
   default 2), `sizing` (an `object({ cpu, memory_mb })` with a default), and
   `region` — **with no default**.
2. **Two validations**: `env` accepts only `dev`, `staging`, `prod`; `replicas`
   stays between 1 and 9. Each block carries its `error_message`, which is
   **mandatory**.
3. **An `env.auto.tfvars` file** setting `env = "prod"`.
4. **`local.stack_name`** equal to `app-<env>-<region>`, computed internally.
5. **A `local_file`** writing `manifest-<stack_name>.json`.
6. **Five outputs**: `env_effectif`, `region_effective`, `stack_name`,
   `sizing_total_mb` and `manifest_path`.

## 🧭 The four rungs, in order

```
default  <  TF_VAR_  <  terraform.tfvars  <  *.auto.tfvars  <  -var
```

The **decisive** rung is the second: a values file **beats** the environment
variable. `TF_VAR_` sits just above the `default`, and below **any** file. That
is the rank almost everyone places too high, and noticing it in production costs
an evening.

The most **discreet** is the third: an `*.auto.tfvars` is loaded automatically,
after `terraform.tfvars`. Its name does not say so, no command mentions it, and
a colleague dropping one into the repository changes everyone's behaviour.

## 🔍 Validation

```bash
dsoxlab check first-infra-variables-outputs
```

Eight tests. The four rungs are checked **in order**, by actually manipulating
the environment and the files. Validations are judged on the **exit code only**:
a message is a string its author chooses, making it a criterion would amount to
grading the wording. A counter-check verifies that an allowed value **passes**,
otherwise a condition refusing everything would make the test pass for the wrong
reason.
