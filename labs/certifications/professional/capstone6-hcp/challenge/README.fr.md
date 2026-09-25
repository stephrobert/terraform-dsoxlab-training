# 🎯 Challenge : l'audit de conformité

## 📦 Point de départ

`challenge/work` contient trois répertoires. **Aucun compte HCP Terraform.**

| Fichier | État |
| --- | --- |
| `audit/situations.auto.tfvars.json` | **fourni**, sept runs décrits |
| `audit/variables.tf`, `audit/versions.tf` | **fournis** |
| `audit/verdicts.tf` | un `???` : le verdict de chaque situation |
| `audit/gouvernance.tf` | trois `???` : des faits à établir |
| `rattachement/versions.tf` | le bloc `cloud` manque |
| `secret/main.tf` | deux `???` : la fiche et son empreinte |
| `secret/variables.tf`, `jeton.auto.tfvars` | **fournis**, à ne pas modifier |

## ✅ Objectif

1. **Qualifier les sept situations.** Sept mots sont possibles ; six suffisent,
   et chacun ne sert qu'une fois.
2. **Établir trois faits** de gouvernance.
3. **Rattacher `rattachement/`** au workspace `audit-conformite` de
   l'organisation `atelier-dsoxlab`, par son nom.
4. **Écrire la fiche de service** sans que le jeton entre dans le state.

Écrivez une **règle**, pas une liste de réponses : aucune clé de situation ne
doit apparaître dans votre expression.

## 🧭 Les règles ne commutent pas

Chaque situation croise deux sous-objectifs. L'ordre dans lequel vous posez les
questions décide du résultat, parce que chacune rend la suivante sans objet :
un workspace qui n'exécute rien n'évalue aucune policy ; un run qui ne pourra
jamais appliquer n'a rien à bloquer ; un plan sans changement n'applique rien.

## ⚠️ Six issues différentes

C'est ainsi que le capstone est bâti, et un test le vérifie. Deux situations qui
recevraient le même verdict signaleraient une règle qui les confond, pas deux cas
qui se ressemblent.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone6-hcp
```

Huit tests. L'audit se lit dans `terraform output -json`, le rattachement dans la
sortie de l'initialisation, et le secret dans le state, balayé en entier.

Bloqué ? `dsoxlab hint certifications-professional-capstone6-hcp`.
