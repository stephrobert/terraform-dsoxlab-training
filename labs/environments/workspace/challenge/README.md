# 🎯 Challenge: one directory, three states

## 📦 Starting point

`challenge/work` is **already initialised** and runs offline (`local`, `random`).

| File | What it is |
| --- | --- |
| `versions.tf`, `outputs.tf` | **complete**, leave them alone |
| `main.tf` | stubbed with `???` |
| `variables.tf` | a `nom_env` variable. **Read its comment** |
| `terraform.tfstate.d/bac-a-sable/` | an **inherited** workspace, already applied |
| `sorties/app-bac-a-sable-0.conf` | the file it produced |
| `CIBLE.md` | the state to reach, and the useful commands |

## ✅ What you must achieve

1. Exactly **three** workspaces: `default`, `dev`, `prod`. `bac-a-sable` is gone.
2. `default` tracks **no** resource.
3. `dev` tracks **2** resources and produces **1** file; `prod` tracks **4** and
   produces **3**.
4. Every file carries the name of the workspace that created it, with **no**
   literal `dev` or `prod` anywhere in the configuration.
5. Neither `dev` nor `prod` has pending changes.
6. `sorties/app-bac-a-sable-0.conf` no longer **exists**.
7. The workspace selected at the end is `default`.

## ⚠️ The heart of the matter

Deleting a workspace **destroys** nothing. Terraform even refuses to do it while
the workspace still tracks resources:

```text
Error: Workspace is not empty
```

The `-force` option overrides that, deletes the **state** and leaves the files on
disk. Nothing manages them any more: they are orphans. The correct order is
**destroy**, then delete.

Second trap: a **variable** does not follow the workspace. The current workspace
name is read from the `terraform.workspace` expression.

## 🔍 Validation

`dsoxlab check environments-workspace` proves, by execution:

- the workspace inventory, read from `terraform.tfstate.d/`;
- the resource and file counts **per workspace**, without touching your own
  selection (thanks to `TF_WORKSPACE`);
- that naming really follows `terraform.workspace`, by applying in a **witness**
  workspace you have never seen;
- convergence of `dev` and `prod`;
- the disappearance of the inherited file;
- the workspace selected at the end, read from `.terraform/environment`.

Stuck? `dsoxlab hint environments-workspace`.
