# Scenario: the lifecycle block decides the order, not you

**Exam objective targeted: 2d.**

The `lifecycle` block is more than four switches: it reorders the graph, it propagates to dependencies in a counter-intuitive direction, and it hosts the only validations that see values resolved at plan time. The trap covered here is twofold: believing `create_before_destroy` propagates towards the resources depending on yours, and believing `prevent_destroy` really protects.

## Capability targeted

Tune an applied configuration's lifecycle so that replacement happens with no outage window, so that a critical piece of data refuses to be destroyed, so that an external drift stops polluting plans without blinding the whole resource, so that a trigger carried by a plain variable forces a replacement, and so that an invalid input fails at plan time rather than at apply time.

## Where the learner starts

`challenge/work` holds neither state nor `.terraform`:

- `versions.tf`: complete, not to be touched. `required_version = ">= 1.15.0"`, `hashicorp/local` and `hashicorp/random` pinned. No paid provider, no VM.
- `variables.tf`: complete. `env` (string, default `"prod"`), `revision` (number, default `1`), `message` (string), `permissions` (string, default `"0644"`).
- `modele.txt`: a fixture read by a `data "local_file" "modele"` block, holding the `{{env}}` token.
- `main.tf`: applicable **as it stands**, with not a single `lifecycle` block. `random_pet.version` carries `keepers = { revision = var.revision }`, `local_file.app` has a `filename` containing `random_pet.version.id`, `local_file.donnees` holds the data to protect, `local_file.journal` has `content = var.message` and `file_permission = var.permissions`, `local_file.marqueur` depends on nothing. The `terraform_data` resource the fifth objective needs does not exist: it is to be written.

There is **no** `lifecycle.tf` file started with `???`. Two reasons, and they are part of the subject: a `lifecycle` block cannot live outside a `resource` block, and `???` is not valid HCL, which would make impossible the initial `apply` the brief imposes as the starting observation. Everything therefore goes into `main.tf`, inside the resources concerned.

The brief requires an `init` then an `apply` before any modification. A `plan -var 'revision=2'` on that version is the starting observation: the new value in place destroys before creating.

## The state to reach

1. `local_file.app` carries `create_before_destroy`, and `random_pet.version`, which it depends on, **does not**: Terraform applies it implicitly, because propagation goes down towards dependencies.
2. `local_file.donnees` refuses any destruction plan while its rule is present in the configuration.
3. `local_file.journal` ignores a `content` change coming from the **configuration**, but keeps planning a permissions change: the `all` shortcut is therefore excluded. A point verified on 1.15.4: `ignore_changes` compares the configuration with state, it does **not** absorb a drift of the file on disk. For `local_file`, an external modification makes the resource vanish from state, and Terraform then plans a creation no `ignore_changes` can suppress.
4. A `terraform_data` resource carries `input = var.revision`, and `local_file.marqueur` is replaced every time that value moves, without depending on any attribute of the marker itself.
5. `local_file.app` refuses at plan time an `env` outside `dev`, `staging`, `prod`, and refuses after creation a content where the `{{env}}` token was not substituted.
6. After the final apply, a plan with no overridden variable proposes nothing.

## How it is proven

The tests drive Terraform and never read the `.tf` files.

- Replacement order: `terraform plan -var 'revision=2' -out` then `terraform show -json` of the plan. `resource_changes[]` for `local_file.app` must carry `actions == ["create", "delete"]`, and not `["delete", "create"]`. The propagation is proven by the same output: `random_pet.version` also carries `["create", "delete"]` although the learner wrote nothing on it. If the learner put the rule on `random_pet.version` instead of `local_file.app`, `local_file.app` stays at `["delete", "create"]` and the test fails.
- Protection: `terraform plan -destroy -json` must exit non-zero and emit a `diagnostic` message, `severity: error`, whose `address` is `local_file.donnees`. The test then re-runs a `plan -destroy` after moving the configuration into a temporary directory stripped of that `resource` block: destruction is planned there without error, which demonstrates the rule's documented limit.
- Ignored drift: the test runs `terraform plan -var 'message=v2' -out` then reads the plan as JSON. `local_file.journal` must carry `actions == ["no-op"]` there. The same test follows with a `plan -var 'permissions=0600'` which must, this time, carry a change on the same resource: the scope is indeed limited to one attribute, and the `all` shortcut would fail that second check. A point measured on 1.15.4: that permissions change produces a **replacement** (`["delete", "create"]`) rather than an in-place update, `local_file` recreating the file. The test therefore only requires the plan not to be `["no-op"]`.
- External trigger: `terraform plan -var 'revision=2' -json` must hold a `resource_changes` entry on `local_file.marqueur` with `actions == ["delete", "create"]` and `action_reason` being exactly **`replace_by_triggers`** (value measured on Terraform 1.15.4; it is the only one proving a `replace_triggered_by`, another would betray a replacement coming from an attribute change). A `replace_triggered_by` pointing directly at `var.revision` cannot produce that plan: Terraform answers `Only resources, count.index, and each.key may be used in replace_triggered_by`.
- Validation: `terraform plan -var 'env=bidon' -json` must produce a `diagnostic` in error carrying the precondition's `error_message` text, with no resource planned. The postcondition is checked on the apply's output with a fixture whose token is not substituted.
- Idempotence: `terraform plan -detailed-exitcode` returns 0 right after the final apply, and `terraform show -json` counts no resource in `mode: managed` beyond the six expected.

None of these checks passes on an empty directory, nor if the learner merely copies the blocks without attaching them to the right resource.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/lifecycle-terraform/
