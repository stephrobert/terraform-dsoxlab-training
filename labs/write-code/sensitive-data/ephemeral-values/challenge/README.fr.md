# 🎯 Challenge : un jeton qui ne touche jamais le state

## Point de départ

`challenge/work` contient un projet cohérent mais incomplet. `versions.tf` et
`variables.tf` sont **fournis, à ne pas modifier** : `longueur` (number) vaut 20.
`main.tf` déclare un `random_password.persistant` (ordinaire), un
`local_file.marqueur` non secret, et un bloc **jeton troué** (`???`).
`outputs.tf` est troué. `terraform apply` échoue en l'état.

## ✅ Objectif

1. **`main.tf`, bloc jeton** : déclarez-le **`ephemeral`**, pour que
   `random_password.jeton` produise une valeur générée pendant l'opération mais
   **jamais écrite** dans le state.
2. **`outputs.tf`, `jeton_masque`** : exposez le résultat du jeton éphémère au
   niveau racine. Un output racine **refuse** une valeur éphémère
   (`Ephemeral value not allowed`) : passez-la par **`ephemeralasnull()`**, qui
   la rend `null`.

Ne faites **pas** fuiter le jeton : le poser dans un attribut persisté (le
`content` du `local_file`, par exemple) lèverait `Invalid use of ephemeral value`.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **Une valeur éphémère n'apparaît nulle part dans le state**, contrairement au
  `random_password.persistant` dont le `result` y est en clair.
- **Un output racine refuse un éphémère** ; `ephemeralasnull()` l'expose en
  `null` sans le divulguer.
- **Un éphémère dans un attribut persisté échoue** au plan.

## 🔍 Validation

```bash
dsoxlab check write-code-sensitive-data-ephemeral-values
```

Quatre tests lisant `terraform show -json` et `output -json` : le seul
`random_password` persistant et son `result` en clair, l'absence totale d'adresse
éphémère dans le state, `jeton_masque` à `null`, et l'idempotence. Aucun ne lit
vos `.tf`.
