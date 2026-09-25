# 🎯 Challenge: destroying cleanly

## Starting point

`challenge/work` holds four resources. Three form a dependency chain, the fourth
is an independent **witness**. The `local_file`'s `lifecycle` block has a hole.

No cloud, no VM, no network call: everything is deterministic and replayable.

## ✅ Objective, in this order

1. **Protect** the `local_file` with the meta-argument forbidding its
   destruction, then apply.
2. **Run a global `destroy`**: it must **fail**. Keep its exit code in
   `artefacts/rc-prevent-destroy.txt`.
3. **Lift the protection**, then export a destroy plan as JSON into
   `artefacts/plan-destroy.json` — without destroying anything.
4. **Destroy in a targeted way** the `null_resource` only.
5. **Remove the witness from the code**, then apply: Terraform destroys it
   because it is no longer declared.
6. **Destroy the rest**.

## 🧭 Four ways to destroy, and what tells them apart

| Gesture | What it does |
|---|---|
| global `destroy` | everything, except what a guard **refuses** |
| `destroy -target` | **only** what you name |
| removing from code | destroyed on the next `apply`, **with no `destroy`** |
| full `destroy` | empties the state, **without deleting its file** |

<Aside type="caution" title="A failing plan still writes a file">
`terraform plan -destroy` on a protected configuration exits with **code 1** and
**still** produces the file requested by `-out`. That plan is **incomplete**:
three resources out of four. You read it, you believe it, and it lies by
omission. That is why step 3 comes **after** lifting the protection.
</Aside>

And one last reflex to lose: **do not delete `terraform.tfstate`** after a
`destroy`. The file carries the project `lineage` and its `serial`; deleting it
makes Terraform start from zero.

## 🔍 Validation

```bash
dsoxlab check first-infra-clean-destroy
```

Five tests. The guard is judged on the **exit code**, not the message: text
changes with versions. The destroy plan is judged on the **number of
addresses**, because a test checking only the file's existence would pass on a
mutilated plan.
