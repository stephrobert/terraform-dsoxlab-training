# 🎯 Challenge: play a run, then qualify six others

## 📦 Starting point

`challenge/work` holds two directories. **No account needed**: the run half is
played locally with saved plans.

| File | State |
| --- | --- |
| `run/versions.tf`, `run/main.tf` | **supplied**, do not change |
| `analyse/situations.auto.tfvars.json` | **supplied**, six runs described |
| `analyse/variables.tf`, `analyse/versions.tf` | **supplied** |
| `analyse/verdicts.tf` | one `???`: each run's outcome |
| `analyse/etapes.tf` | one `???`: the eleven stages, in order |
| `analyse/faits.tf` | three `???`: facts to establish |

## ✅ Objective

1. **Play a first run** in `run/`: save its plan as `run1.tfplan` with the
   message `premier-run`, then apply **that plan**.
2. **Plan a second run** into `run2.tfplan` with the message `second-run`, and
   **leave it pending**. It is a run stopped at "Needs Confirmation": planned,
   not applied.
3. **Keep both plan files.** They are what proves the work.
4. **Qualify the six runs**, with five words and no more: `plan_speculatif`,
   `planned_and_finished`, `apply_automatique`, `attend_confirmation`,
   `aucun_run_distant`.
5. **Order the eleven stages**, and **establish three facts**.

## 🧭 Try what is refused

Once the first run is applied, try replaying its plan. And try passing a `-var`
to the apply of the second one. Both are refused, and each refusal has a
counterpart in HCP Terraform: a workspace's run queue, and a run locked to its
set of variable values.

Those two error messages are worth reading in full. They say more about what a
run is than any definition.

## ⚠️ No constant answer passes

| Uniform answer | Fails on |
| --- | --- |
| `attend_confirmation` everywhere | the four other cases |
| `apply_automatique` everywhere | five of the six |
| `plan_speculatif` everywhere | five of the six |

Two traps in particular: the auto-apply setting does not make a pull request
apply anything, and it does not apply a plan that holds no changes.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-hcp-terraform-overview
```

Fifteen tests. The run half reads the disk and the saved plans through
`terraform show -json`; the rest reads `terraform output -json`, so what your
configuration **computes**, never what it contains.

Stuck? `dsoxlab hint hcp-terraform-hcp-terraform-overview`.
