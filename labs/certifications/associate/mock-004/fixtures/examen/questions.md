# Mock exam: Terraform Associate 004

Forty questions, labelled by official sub-objective. Answer in
`reponses.auto.tfvars`, one entry per question.

| Type | What is expected |
| --- | --- |
| single choice | **one** letter, for example `b` |
| true / false | `v` or `f` |
| multiple choice | the letters **sorted**, stuck together, for example `ac` |
| workshop | the value read in `atelier/`, lowercase |

The last four questions have no answer **until** `atelier/` has been built and
applied. They are about the state it produces.

Case and spaces around the answer are ignored.

---

## q01 — objective 1a — single choice

What most reliably distinguishes infrastructure as code from a provisioning script?

- **a.** the language used is declarative rather than imperative
- **b.** the tool maintains a state that lets it converge towards the described target
- **c.** the code is stored in a Git repository
- **d.** execution is idempotent

## q02 — objective 1b — multiple choice

Which of these advantages are directly brought by an IaC practice? (several answers)

- **a.** peer review of infrastructure changes
- **b.** the complete elimination of production outages
- **c.** reproducing an environment identically
- **d.** a guarantee that the provider will not change its API

## q03 — objective 2a — single choice

Which file freezes the provider versions actually installed, with their checksums?

- **a.** .terraform/providers.json
- **b.** .terraform.lock.hcl
- **c.** versions.tf
- **d.** terraform.tfstate

## q04 — objective 2a — single choice

The lock file's checksums are recorded:

- **a.** once, valid for every platform
- **b.** per platform, which makes `terraform providers lock -platform=...` necessary for a heterogeneous team
- **c.** per Terraform version
- **d.** for official HashiCorp providers only

## q05 — objective 2b — true / false

`required_version` in the `terraform` block also constrains provider versions.

## q06 — objective 2d — single choice

What is Terraform's state for?

- **a.** storing the credentials used to reach the provider
- **b.** mapping every real object to the address that declares it, and remembering its attributes
- **c.** keeping a history of every apply
- **d.** replacing the lock file

## q07 — objective 3b — single choice

What does `terraform init` do besides downloading the providers?

- **a.** it applies the configuration
- **b.** it parses the configuration, and therefore fails on a syntax error
- **c.** it checks the resources exist at the provider
- **d.** it deletes the local state

## q08 — objective 3c — true / false

`terraform validate` can usefully run before `terraform init`.

## q09 — objective 3c — single choice

Which of these defects does `terraform validate` catch?

- **a.** an argument value the provider's API refuses
- **b.** an attribute that exists in no provider's schema
- **c.** a resource deleted by hand at the provider
- **d.** a lock conflict on the remote state

## q10 — objective 3d — single choice

`terraform plan -detailed-exitcode` returns 2. That means:

- **a.** the command failed
- **b.** there is no change
- **c.** the plan succeeded and holds changes
- **d.** the state is locked

## q11 — objective 3e — single choice

Applying a plan saved with `-out` guarantees:

- **a.** the apply asks for no confirmation and applies exactly that plan
- **b.** the apply re-reads the configuration when applying
- **c.** the state will not be modified
- **d.** data sources will not be re-read

## q12 — objective 3f — true / false

`terraform destroy` deletes the `terraform.tfstate` file.

## q13 — objective 3g — single choice

`terraform fmt -check` on a file outside canonical format returns the code:

- **a.** 1
- **b.** 2
- **c.** 3
- **d.** 0 with a warning

## q14 — objective 4a — single choice

What fundamental difference separates a `data` block from a `resource` block?

- **a.** a `data` block cannot be used with `for_each`
- **b.** a `data` block reads without creating, and appears in no destruction plan
- **c.** a `data` block never appears in state
- **d.** a `data` block cannot depend on a resource

## q15 — objective 4b — true / false

Referencing a resource attribute creates an implicit dependency, and waits for that resource to have finished being applied.

## q16 — objective 4c — single choice

Among these value sources, which one prevails over all the others?

- **a.** the TF_VAR_ environment variable
- **b.** the terraform.tfvars file
- **c.** an *.auto.tfvars file
- **d.** the -var command-line option

## q17 — objective 4c — single choice

A variable is set both by TF_VAR_ and by terraform.tfvars. Which one wins?

- **a.** TF_VAR_, because an environment variable overrides a file
- **b.** terraform.tfvars, because values files are loaded afterwards
- **c.** it depends on alphabetical order
- **d.** Terraform refuses to plan and asks you to decide

## q18 — objective 4d — single choice

`for_each` accepts:

- **a.** a list or a set
- **b.** a map or a set of strings
- **c.** any collection
- **d.** a number

## q19 — objective 4d — true / false

On a resource driven by `for_each`, the splat syntax `[*]` raises an error.

## q20 — objective 4e — single choice

`element(["dev","staging","prod"], 5)` returns:

- **a.** an index out of range error
- **b.** "dev"
- **c.** "prod"
- **d.** null

## q21 — objective 4e — single choice

`lookup({dev = "small"}, "qa")`, with no third argument, returns:

- **a.** null
- **b.** an empty string
- **c.** an error
- **d.** "small"

## q22 — objective 4f — single choice

When is `depends_on` justified?

- **a.** whenever a precise order is wanted
- **b.** when the resource uses none of the upstream's data and depends on it anyway
- **c.** when the resource already references an attribute of the upstream
- **d.** to force a data source to be re-read

## q23 — objective 4g — multiple choice

Among these mechanisms, which ones STOP Terraform when their condition is false? (several answers)

- **a.** a variable's `validation` block
- **b.** a `lifecycle` block's `precondition`
- **c.** the root-level `check` block
- **d.** a `lifecycle` block's `postcondition`

## q24 — objective 4h — single choice

Which statement correctly describes `sensitive = true` on an output?

- **a.** the value is encrypted in state
- **b.** the value is masked on display and stays in clear text in state
- **c.** the value is removed from state
- **d.** the value is only readable by the workspace owner

## q25 — objective 5a — single choice

Which module source does NOT download from the network?

- **a.** a local path starting with ./ or ../
- **b.** the Terraform Registry
- **c.** a Git repository
- **d.** an S3 bucket

## q26 — objective 5b — true / false

A child module automatically inherits the variables declared in the root module.

## q27 — objective 5c — single choice

A module intended to be called several times:

- **a.** must declare its own `provider` blocks
- **b.** must contain no `provider` block, the configurations being passed by its caller
- **c.** must carry a `count`
- **d.** cannot declare `required_providers`

## q28 — objective 5d — single choice

The `version` argument of a `module` block can be used:

- **a.** for every module source
- **b.** only for modules coming from a registry
- **c.** only for local modules
- **d.** only with HCP Terraform

## q29 — objective 6a — true / false

Without a `backend` block, Terraform writes terraform.tfstate in the working directory.

## q30 — objective 6b — single choice

What is state locking for?

- **a.** encrypting state at rest
- **b.** preventing two concurrent operations from writing state at the same time
- **c.** preventing resources from being destroyed
- **d.** locking provider versions

## q31 — objective 6c — true / false

A `backend` block can reference an input variable for its path or its bucket.

## q32 — objective 6d — single choice

Which command aligns state with reality WITHOUT modifying the infrastructure?

- **a.** terraform apply -refresh-only
- **b.** terraform apply -auto-approve
- **c.** terraform state rm
- **d.** terraform force-unlock

## q33 — objective 6d — single choice

A `removed` block carrying `lifecycle { destroy = false }`:

- **a.** destroys the object and drops it from state
- **b.** drops the resource from state while leaving the object in place
- **c.** prevents any future destruction
- **d.** renames the resource in state

## q34 — objective 7a — true / false

An import is finished as soon as the resource appears in `terraform state list`.

## q35 — objective 7c — single choice

To isolate a debug trace in a file rather than on the terminal:

- **a.** TF_LOG=DEBUG alone is enough
- **b.** TF_LOG=DEBUG together with TF_LOG_PATH
- **c.** terraform plan -debug
- **d.** terraform plan > trace.log

## q36 — objective 8c — single choice

In HCP Terraform, a project is used to:

- **a.** store provider versions
- **b.** group workspaces together and carry common permissions
- **c.** replace the lock file
- **d.** run plans locally

## q37 — objective 7b — workshop

In `atelier`, how many objects does state hold in `mode: managed`? (a number, read from `terraform show -json`)

## q38 — objective 7b — workshop

In `atelier`, what is the full address of the only `mode: data` block? (for example `data.type.name`)

## q39 — objective 7b — workshop

In `atelier`, what code does `terraform plan -detailed-exitcode` return right after the apply? (a digit)

## q40 — objective 4h — workshop

In `atelier`, does the value of the output marked `sensitive` appear in clear text in `terraform.tfstate`? (v or f)
