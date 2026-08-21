# 🎯 Challenge : source explicite et alias

## Point de départ

`challenge/work` contient un projet incomplet, `versions.tf` et `main.tf`, tous
deux troués (`???`). Seul `hashicorp/random` est utilisé. `terraform apply`
échoue en l'état.

## ✅ Objectif

1. **`versions.tf`, `source`** : écrivez l'adresse source **explicite** du
   provider random (`hashicorp/random`), même si le préfixe est implicite pour
   les providers HashiCorp.
2. **`main.tf`, second bloc provider** : ajoutez un **`alias = "secondaire"`**.
   Sans lui, ce serait un doublon refusé (`Duplicate provider configuration`).
3. **`main.tf`, `random_pet.autre`** : rattachez cette ressource à la
   configuration aliasée avec **`provider = random.secondaire`**. Ne touchez pas
   à `random_pet.defaut`, qui reste sur la configuration par défaut.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **La source explicite se résout** en `registry.terraform.io/hashicorp/random`.
- **L'alias** crée une seconde configuration du même provider ; une ressource ne
  la prend que si elle porte `provider =`.
- **Le câblage se lit dans le plan JSON** (`provider_config`,
  `provider_config_key`), jamais dans vos `.tf`.

## 🔍 Validation

```bash
dsoxlab check write-code-providers
```

Cinq tests lisant `terraform version -json`, le plan JSON et `show -json` : la
source résolue, la configuration aliasée déclarée, le câblage des deux
ressources, leur présence, et l'idempotence. Aucun ne lit vos `.tf`.
