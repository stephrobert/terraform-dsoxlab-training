# The value that wins

## The situation

**Exam objective targeted: 2e (declare and consume variables and outputs,
including complex types and value precedence).**

One variable is set by five sources that contradict each other. The learner must
make the project able to say which one prevails, and prove it without reading
back a single line of HCL.

## Capability targeted

Parameterise a Terraform configuration with typed variables, one of them a
complex type, constrain their values with a `validation` block, expose results
through `output` blocks, and predict the value actually retained when `default`,
`TF_VAR_*`, `terraform.tfvars`, `env.auto.tfvars` and `-var` conflict. The trap
is the real rank of `TF_VAR_*`: it sits just above the `default`, hence **below**
every values file, contrary to the intuition that "an environment variable
overrides a file".

## Where the learner starts

`challenge/work/` holds an incomplete project. No VM, no remote provider: only
`hashicorp/local` and `hashicorp/random` are used, with a `terraform init` and a
`.terraform.lock.hcl` already in place. The lab runs anywhere `terraform` is on
the PATH, without network access.

The directory holds `versions.tf` (already correct), `variables.tf`,
`locals.tf`, `main.tf`, `outputs.tf` and a `terraform.tfvars` that fixes `env`
and stays silent about `region`. Everything else is holed:

```hcl
variable "env" {          # string, default "dev"
  type       = ???
  validation {            # accept only dev, staging, prod
    condition     = ???
    error_message = "???"
  }
}
variable "replicas" { ??? }  # number, default 2, range 1 to 9
variable "sizing"   { ??? }  # object({ cpu = number, memory_mb = number })
variable "region"   { ??? }  # string, NO default: TF_VAR_ or -var
```

`terraform plan` fails as it stands: the `???` are not valid HCL.

## The state to reach

1. The four variables are typed and described. `sizing` is an
   `object({ cpu = number, memory_mb = number })` with a `default`.
2. `env` rejects any value outside `dev`, `staging`, `prod`. `replicas` rejects
   anything outside 1 to 9. Each `validation` block carries its `error_message`,
   which is mandatory.
3. `terraform.tfvars` sets `env = "staging"` and says nothing about `region`.
4. An `env.auto.tfvars` file sets `env = "prod"`, loaded automatically.
5. `local.stack_name` is `app-<env>-<region>`, computed internally, never
   supplied from outside.
6. `main.tf` writes `manifest-<stack_name>.json` through `local_file`.
7. `outputs.tf` exposes `env_effectif`, `region_effective`, `stack_name`,
   `sizing_total_mb` (memory multiplied by replicas) and `manifest_path`.
8. The project converges: a second plan right after the apply proposes nothing.

## How it is proven

The tests never open the learner's `.tf` files and parse no human error message.
They run Terraform inside `challenge/work` and read only JSON or exit codes.

1. `TF_VAR_region=eu-west-1 terraform apply -auto-approve` then
   `terraform output -json`: `region_effective` is `eu-west-1`. `TF_VAR_*` does
   cover a variable with no `default`.
2. With `env.auto.tfvars` set aside, `TF_VAR_env=dev terraform apply
   -auto-approve` then `terraform output -json`: `env_effectif` is `staging`.
   **The `terraform.tfvars` file beats the environment variable**, the lab's
   decisive rung.
3. `env.auto.tfvars` put back, same command: `env_effectif` is `prod`. The
   `auto` file beats `terraform.tfvars`.
4. `terraform apply -var 'env=dev' -auto-approve`: `env_effectif` is `dev`. The
   flag beats everything else. All four rungs are checked in order.
5. `terraform output -json`: `sizing_total_mb` is a number equal to `memory_mb`
   multiplied by `replicas`, which proves the complex type is really consumed.
6. `terraform plan -var 'env=qa'` exits non-zero, and so does
   `terraform plan -var 'replicas=0'`. Only the exit code is checked.
7. `terraform show -json`: a `local_file` resource exists and its path contains
   the expected `stack_name`.
8. `terraform plan -detailed-exitcode` returns 0 right after the apply. A code 2
   fails the lab.

## 🎯 Challenge: variables, locals and the real precedence

### Starting point

`challenge/work` holds an incomplete project. **No remote provider, no VM**: the
lab runs anywhere `terraform` is on the `PATH`, without network.

`versions.tf` is already correct. `variables.tf`, `locals.tf`, `main.tf` and
`outputs.tf` are **full of holes**. `terraform.tfvars` is provided: it sets
`env` and stays **silent about `region`**.

`terraform plan` fails as is: the `???` are not valid HCL.

### ✅ Objective

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

### 🧭 The four rungs, in order

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

### 🔍 Validation

```bash
dsoxlab check first-infra-variables-outputs
```

Eight tests. The four rungs are checked **in order**, by actually manipulating
the environment and the files. Validations are judged on the **exit code only**:
a message is a string its author chooses, making it a criterion would amount to
grading the wording. A counter-check verifies that an allowed value **passes**,
otherwise a condition refusing everything would make the test pass for the wrong
reason.
