# 🎯 Challenge : exposer un secret sans le divulguer

## Point de départ

`challenge/work` contient un projet cohérent mais incomplet. `versions.tf`,
`variables.tf` et `main.tf` sont **fournis, à ne pas modifier** : `main.tf`
déclare `random_password.admin` et un `local_file.rapport` **non secret** (il
n'écrit que la longueur). La variable `longueur_mot_de_passe` (number) vaut 24
par défaut.

`outputs.tf` est **troué** (`???`) sur trois outputs. `terraform plan` échoue en
l'état.

## ✅ Objectif

1. **`mot_de_passe_admin`** : exposer `random_password.admin.result`, contraindre
   son `type` à `string`, et le marquer **`sensitive`**. Sans cela, le plan est
   refusé (« Output refers to sensitive values »).
2. **`resume`** : contraindre son `type` à
   `object({ longueur = number, empreinte = string })`, non sensible. `longueur`
   vaut `var.longueur_mot_de_passe` ; `empreinte` est le `sha256` du mot de passe.
   Comme le `sha256` d'un secret **reste sensible**, déclassifiez-le avec
   **`nonsensitive()`**. N'exposez **jamais** le mot de passe en clair.
3. **`empreinte_rapport`** : la `value` est déjà écrite ; ajoutez un bloc
   **`precondition`** (avec `error_message`) qui exige
   `var.longueur_mot_de_passe >= 20`.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **`sensitive` ne cache le secret que dans l'affichage humain.**
  `terraform output -json`, `-raw` et le state le rendent **en clair**.
- **La sensibilité se propage**, même à travers `sha256` : sans
  `nonsensitive()`, l'empreinte reste sensible et `resume` échoue ou devient
  sensible.
- **Un output n'est pas passif** : son `precondition` bloque le plan.

## 🔍 Validation

```bash
dsoxlab check write-code-outputs
```

Huit tests lisant `terraform show -json`, `output -json`, `output -raw` et des
codes retour : le drapeau `sensitive`, la valeur en clair dans l'output, le state
et `-raw`, la contrainte de type de `resume` et l'absence de secret, l'empreinte,
le `precondition`, et l'idempotence. Aucun ne lit vos `.tf`.
