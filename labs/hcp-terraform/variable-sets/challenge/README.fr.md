# 🎯 Challenge : classer quinze sources, et tenir sur des cas inconnus

## 📦 Le point de départ

`challenge/work` contient une configuration qui s'applique déjà, sans
infrastructure distante. **Aucun compte HCP Terraform n'est requis.**

| Fichier | État |
| --- | --- |
| `VOCABULAIRE.md` | les quinze identifiants admis, **dans le désordre** |
| `variables.tf`, `versions.tf`, `cas.auto.tfvars` | **fournis** |
| `precedence.tf` | onze `???` sur quinze entrées, quatre **ancres** |
| `resolution.tf` | la résolution et le duel lexical, à écrire |
| `qcm.tf` | cinq affirmations à trancher |

Les quatre ancres (`cli_var`, `tf_var_env`, `workspace`, `terraform_tfvars`)
interdisent de deviner la table en la faisant tourner d'un cran.

## ✅ Objectif

1. **La table complète**, du plus prioritaire au moins.
2. **La résolution** : pour chaque cas, la source retenue **et** sa valeur.
3. **Un cas sans aucune source** résout sur la sentinelle, jamais sur `null` ni
   sur une erreur de plan.
4. **Le duel lexical** : départager deux sets identiques par points de code.
5. **Les cinq affirmations**, en booléens.

## 🧭 L'inversion, et c'est tout le sujet

Chez les variable sets **normaux**, la portée la plus **étroite** gagne.
Chez les **prioritaires**, c'est la plus **large**.

> When a variable set is priority, the values take precedence over any variables
> with the same key set at a more specific scope.

Et deux autres surprises : les fichiers sont **en bas** de la table, et une map
HCL **n'a pas d'ordre** — c'est le nom qui départage, pas l'ordre d'écriture.

## ⚠️ Une résolution écrite cas par cas ne passera pas

Les six cas fournis se résolvent à la main. Les tests en génèrent **huit
autres**, que vous ne verrez pas, dont deux visent l'inversion et un est vide.

Parcourez `local.ordre`. Ne nommez aucun cas.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-variable-sets
```

Douze tests. La table est comparée **position par position**, et le message
nomme le rang fautif. Aucun test ne lit vos `.tf` ni vos `.tfvars`.

Bloqué ? `dsoxlab hint hcp-terraform-variable-sets`.
