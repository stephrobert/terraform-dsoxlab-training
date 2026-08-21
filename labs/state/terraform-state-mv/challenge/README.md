# 🎯 Challenge: reattach three existing objects, destroying none

## ✅ Objective

`challenge/work` holds a project **already applied** by the previous team, whose
code was refactored **without anyone touching the state**. The three objects
exist, but at the **old** addresses:

| In the state (old) | In the code (new) |
| --- | --- |
| `random_pet.web` | `random_pet.frontend` |
| `random_integer.web_port` | `random_integer.frontend_port` |
| `random_string.db_secret` | `module.secret.random_string.this` |

Start by measuring the damage:

```bash
terraform init
terraform plan     # 3 to add, 0 to change, 3 to destroy
```

Now reconcile, with **the right method for each case**:

1. **The two root renames** are handled **imperatively**, with
   `terraform state mv`: the code is already written, only the state lags behind.
2. **The move into the module** is handled **declaratively**, by completing the
   `moved` block in **`moved.tf`** (the only file to modify), then applying.

Then apply, and check the plan proposes nothing any more.

**Do not delete the `moved` block after the apply.** It must stay in the code:
removing it is a breaking change, and the tests check that.

Two files are off limits: `main.tf` and `modules/secret/main.tf` are the
refactored code, and `reference/etat-initial.tfstate` is the frozen copy of the
starting state, used as the tests' reference.

## 🔍 Validation

`dsoxlab check state-terraform-state-mv` proves, by execution:

- the state carries **exactly** the three new addresses, and **none** of the old
  ones;
- the **original identifiers** survived, compared with
  `reference/etat-initial.tfstate`: `random_pet`, `random_integer` and
  `random_string` draw fresh values on every creation, so a single divergence
  would signal a recreation;
- `plan -detailed-exitcode` returns **0**: code and state converge;
- the third move really was **declarative**. The test replays it in a copy: it
  brings the object back to its old address, plans again, and requires a
  `previous_address` carrying a `no-op`. Terraform writes that field **only** when
  a `moved` block was taken into account, never after a `state mv`;
- negative check: with the `moved` block removed, the same plan goes back to
  `delete` plus `create`, which is exactly the breaking change the documentation
  describes.

Stuck? `dsoxlab hint state-terraform-state-mv`.
