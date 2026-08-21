# 🎯 Challenge: decide, split, rewire

## 📦 Starting point

`challenge/work` holds four directories, none of them initialised.

| Directory | What it is |
| --- | --- |
| `mono/` | the configuration to **arbitrate**. READ ONLY: do not apply it |
| `socle/` | the platform root, both its `output` blocks are stubbed |
| `app/` | the application root, its `data` block is stubbed |
| `bac-a-sable/` | the case where workspaces remain legitimate, `lookup` stubbed |
| `CIBLE.md` | the decision criterion and the state to reach |

## ✅ What you must achieve

1. `socle/` applied, tracking at least one resource, exposing **two** non-empty
   outputs.
2. `app/` applied, its state containing a `mode: data` resource of type
   `terraform_remote_state`.
3. An output of `app/` **matches exactly** the platform's value.
4. `socle/` and `app/` manage **disjoint** resources.
5. Neither `socle/` nor `app/` uses a workspace.
6. `bac-a-sable/` has **two** workspaces, `dev` and `prod`, both applied.
7. The size is **2** under `dev` and **8** under `prod`.
8. All **four** states are stable.

## ⚠️ The heart of the matter

Read `mono/main.tf` before writing any code. The header comment says it all:
production is run by **another team**, with its own rights on the state storage.

Now, a `backend` block **cannot reference any named value**:

```text
Error: Variables not allowed
```

The backend is therefore the **same** for every workspace in a directory.
Whatever needs distinct rights on the **state** no longer belongs in workspaces,
and must become a separate **configuration**.

What varies only by **size**, on the other hand, sits perfectly well in a
workspace: that is the case of `bac-a-sable/`.

## 🔍 Validation

`dsoxlab check environments-when-to-use-workspaces` proves, by execution:

- that `app/` really reads the platform's **state**, through a `mode: data`
  entry;
- that the value **crosses** both states: the check replays the platform with a
  different network range, in a copy, and requires `app/` to **follow**. A
  hard-coded value stays frozen and fails;
- that both roots manage **disjoint** resources;
- that neither of them uses a workspace;
- that the sandbox does have its two workspaces, with the right size on each
  side;
- that all four states have converged.

Stuck? `dsoxlab hint environments-when-to-use-workspaces`.
