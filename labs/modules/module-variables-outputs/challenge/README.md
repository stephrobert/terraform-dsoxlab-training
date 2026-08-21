# 🎯 Challenge: write the interface of a module called twice

## 📦 Starting point

`challenge/work` holds a module, `modules/artefact/`, called **twice** from the
root. The module body works; its **interface** is what you must write.

| File | State |
| --- | --- |
| `versions.tf`, `main.tf` | complete, **do not touch** |
| `modules/artefact/main.tf` | complete, **do not touch** |
| `modules/artefact/variables.tf` | three variables, **to write** |
| `modules/artefact/outputs.tf` | three outputs, **to write** |
| `outputs.tf` | two root outputs, **to write** |

The two calls in `main.tf` are your **specification**:

```hcl
module "complet" {
  depot           = { nom = "archives", retention_jours = 30, chiffre = true }
  etiquette       = "production"
  longueur_secret = 24
}

module "minimal" {
  depot = { nom = "livraison" }
}
```

The **minimal** call is what puts the interface to the test: it provides one
attribute out of three, and neither of the other two variables.

## ✅ Objective

Write an interface that **absorbs** that difference, **refuses** unacceptable
values, and **protects** what must be protected.

## 📋 What you must obtain

1. The minimal call succeeds: `retention_jours` is **7** and `chiffre` is
   **true** without the caller providing them.
2. A call passing `etiquette = null` still gets `"artefact"`: the variable
   **refuses null** instead of propagating it.
3. `longueur_secret = 8` is **rejected**, with a message naming the bounds `12`
   and `64`.
4. The `resume` output exposes `nom`, `retention_jours`, `chiffre` and
   `etiquette`, filled-in defaults included.
5. The generated secret reaches the root **without being readable** in ordinary
   output, and has the length the complete call asked for.
6. The `chemin` output **refuses to publish itself** when the repository is not
   encrypted: the plan stops.
7. `terraform plan -detailed-exitcode` exits **0** after the apply.

## ⚠️ The heart of the matter

`type` and `default` are not enough. Four mechanisms complete the interface:

| Need | Mechanism |
| --- | --- |
| An optional **object attribute** | `optional(type, default)` |
| An **explicit `null`** that must yield the default | `nullable = false` |
| An **out-of-range value** refused | `validation` block |
| An output that **refuses to publish** | `precondition` block |

And a fifth, which you only discover by hitting it: a value derived from a
`random_password` **contaminates** whatever it crosses. A root output
republishing it without declaring so makes the **plan fail**.

## 🔍 Validation

`dsoxlab check modules-module-variables-outputs` proves, by execution:

- the state holds both `module.complet` and `module.minimal`: a flat
  configuration fails;
- `resume_minimal` is exactly
  `{"nom": "livraison", "retention_jours": 7, "chiffre": true, "etiquette": "artefact"}`;
- in a **copy** of the project where the minimal call receives
  `etiquette = null`, the label stays `"artefact"`;
- in a copy with `longueur_secret = 8`, `terraform validate -json` returns
  `valid: false` with `Invalid value for variable`;
- `secret_partage` is marked sensitive and is 24 characters long; removing that
  marking in a copy makes the plan fail;
- in a copy with `chiffre = false`, the plan fails on an output
  **precondition**;
- `plan -detailed-exitcode` returns **0**.

Faulty variants are produced in **temporary copies**: your work is never
modified.

Stuck? `dsoxlab hint modules-module-variables-outputs`.
