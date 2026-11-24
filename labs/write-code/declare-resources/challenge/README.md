# A resource's lifecycle is read in the plan

## The situation

**Exam objective targeted: 1c.**

Declaring a `resource {}` block is trivial; saying, before applying, whether
Terraform will update in place or destroy then recreate is not. Trap covered:
`depends_on` everywhere, whereas the official documentation ranks it as a last
resort.

## Capability targeted

Build a configuration of four resources whose creation order follows from
references alone, obtain a replacement with creation before destruction, and
prove in the JSON plan the difference between `update`, `create` then `delete`,
and the reverse.

## Where the learner starts

`challenge/work` holds four files, no state, no `.terraform`:

- `versions.tf` and `variables.tf`: complete, not to be touched. The `local` and
  `random` providers pinned, `required_version >= 1.15.0`, variables `etiquette`
  (string, default `"v1"`) and `generation` (number, default `1`).
- `main.tf`: four `resource {}` blocks started, `???` on the labels, on the
  references between resources, on the `lifecycle` block, on the dependency
  meta-argument. `outputs.tf`: two `output` blocks whose values are `???`.
  Those `???` are syntax errors: nothing applies as it stands.

## The state to reach

1. State holds exactly four resources in `mode: managed`, at addresses
   `random_pet.hote`, `local_file.fiche`, `terraform_data.sceau`, `local_file.journal`.
2. `local_file.fiche` draws its content from `random_pet.hote.id`: an implicit
   dependency, with no `depends_on`, and carries `create_before_destroy = true`.
3. `terraform_data.sceau` carries `input = var.etiquette` and
   `triggers_replace = random_pet.hote.id`; `random_pet.hote` has `keepers` tied
   to `generation`.
4. `local_file.journal` depends on `terraform_data.sceau` through `depends_on`
   alone, referencing no attribute: a behavioural dependency, the only justified
   case.
5. The outputs expose the fiche's path and `terraform_data.sceau.output`, and an
   `apply` followed by a `plan` proposes no change.

## How it is proven

The tests drive Terraform and never read the `.tf` files. No check passes on an
empty directory, nor without the references wired.

- `terraform show -json`: `values.root_module.resources` holds the four
  addresses, all in `mode: managed`; in `configuration.root_module.resources`,
  `depends_on` is present on `local_file.journal` and absent on
  `local_file.fiche`.
- `terraform output -json`: both outputs exist, and the seal's value equals the
  applied label. `terraform plan -detailed-exitcode` exits 0 right after the
  apply, which proves idempotence.
- `terraform plan -var 'etiquette=v2' -json`: the planned action for
  `terraform_data.sceau` is `["update"]`, the in-place update.
- `terraform plan -var 'generation=2' -json`: `random_pet.hote` is replaced,
  `terraform_data.sceau` too by propagation of the trigger, and
  `local_file.fiche` shows `["create", "delete"]` in that order, the signature of
  `create_before_destroy`, where the absence of the rule would give
  `["delete", "create"]`.

Reference: https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/declarer-ressources/ (in French)

## 🎯 Challenge: four resources, four operations

### Starting point

`challenge/work` holds four `resource {}` blocks and two `output` blocks, all
holed with `???`. `versions.tf` and `variables.tf` are **complete, not to be
modified**: they declare the variables `etiquette` (string) and `generation`
(number).

The `???` are syntax errors: `terraform init` fails as it stands. Every hole
carries above it a comment stating what is expected.

### ✅ Objective

Wire the configuration so that state holds exactly four managed resources, at
addresses `random_pet.hote`, `local_file.fiche`, `terraform_data.sceau`,
`local_file.journal`:

1. **`random_pet.hote`** carries `keepers` tied to `var.generation`: a change of
   generation must replace it.

2. **`local_file.fiche`** draws the host's id into its `filename` (an
   **implicit** dependency, with no `depends_on`), and carries
   `create_before_destroy = true`.

3. **`terraform_data.sceau`** carries `input = var.etiquette` (an in-place update
   when the label changes) and `triggers_replace` holding the host's id (a
   replacement when it changes).

4. **`local_file.journal`** depends on the seal through `depends_on` **alone**,
   referencing none of its data: that is a behavioural dependency.

5. The outputs expose the fiche's path and the seal's `output` attribute.

After your `apply`, `terraform plan` must propose nothing.

### 🧭 What the tests read

The JSON plan's `resource_changes[].actions` array. The tests check the
signatures of the four operations:

- `etiquette=v2`: the seal must be at **`["update"]`** (in-place update).
- `generation=2`: the fiche must be at **`["create", "delete"]`**
  (`create_before_destroy`), not `["delete", "create"]`.

Badly wired blocks do not produce those signatures.

### 🔍 Validation

```bash
dsoxlab check write-code-declare-resources
```

Seven tests. They decode `terraform show -json` (state and configuration),
`output -json` and the JSON plan. None reads your `.tf`.
