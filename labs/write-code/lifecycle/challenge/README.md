# 🎯 Challenge: the `lifecycle` block decides the order, not you

## The starting point is imposed

`challenge/work` holds a configuration **that applies as it stands** and that
contains **no** `lifecycle` block. Before any modification:

```bash
terraform init
terraform apply
terraform plan -var 'revision=2'
```

That last plan is your starting observation: Terraform **destroys before
creating**. There is therefore a window during which the file does not exist.

Do not touch `versions.tf`, `variables.tf` or `modele.txt`. Everything happens in
`main.tf`.

## ✅ Objective

1. **Remove the outage window.** `local_file.app` must be created before being
   destroyed during a replacement. Write **nothing** on `random_pet.version`:
   Terraform must apply the rule to it by itself. If you have to write it by
   hand, you placed it in the wrong spot.

2. **Protect the critical data.** `local_file.donnees` must make
   `terraform plan -destroy` fail.

3. **Silence the journal's drift, and no more.** A `content` change coming from
   the configuration must plan nothing on `local_file.journal` any more. A
   `permissions` change, however, must keep being planned. The shortcut that
   ignores everything is therefore excluded.

4. **Trigger a replacement from a bare value.** `local_file.marqueur` depends on
   no moving attribute. It must nonetheless be replaced every time `revision`
   changes. Careful: `replace_triggered_by` only accepts **managed resources**. A
   variable or a local are refused by Terraform, with the message `Only
   resources, count.index, and each.key may be used in replace_triggered_by`. So
   you are missing a resource.

5. **Refuse an invalid input at plan time.** An `env` outside `dev`, `staging`,
   `prod` must fail the plan. And after creation, a content where the `{{env}}`
   token was not substituted must be reported. Both checks must live **inside
   the resource**, not on the variable: a `validation` block would filter the
   value all right, but does not answer the brief (the tests read
   `checks[].address.kind`).

After your last `apply`, `terraform plan` must propose nothing.

## 🧭 Two traps to know

- **The `lifecycle` block only accepts literal values.** All its rules serve to
  build the dependency graph, which happens too early to evaluate an expression.
  `prevent_destroy = var.protege` answers `Variables not allowed`.
- **`ignore_changes` compares the configuration with state**, not with what is on
  disk. Changing the file by hand outside Terraform will not be absorbed.

## 🔍 Validation

```bash
dsoxlab check write-code-lifecycle
```

Twelve tests. They drive Terraform and read the plan as JSON
(`resource_changes[].actions`, `action_reason`) as well as the `checks` array.
None reads your `.tf` files: copying blocks without attaching them to the right
resource does not pass.
