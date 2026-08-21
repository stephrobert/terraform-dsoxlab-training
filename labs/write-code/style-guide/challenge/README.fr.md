# 🎯 Challenge : rendre une configuration acceptable en CI

## Point de départ

`challenge/work` contient un projet en **un seul fichier `infra.tf`**, plus un
`terraform.tfvars` (`replica_count = "3"`, entre guillemets). La configuration
**fonctionne** dans son intention, mais elle est dégradée sur cinq axes et ne
passerait aucune CI :

- **formatage** : indentation à 4 espaces, `=` non alignés (`fmt -check` code 3) ;
- **cohérence** : le contenu référence `var.env_name`, jamais déclarée (la
  variable existante est `environment`), donc `validate` échoue ;
- **nommage** : ressources en camelCase répétant leur type
  (`localFileAppConfig`, `randomPetInstanceName`) ;
- **typage** : variables sans `type` ni `description` ;
- **sensibilité** : outputs sans `description`, jeton d'API non `sensitive`.

## ✅ Objectif

Rendre la configuration conforme, **sans changer les ressources créées** :

1. `terraform fmt` passe sans rien signaler.
2. `validate` est vert : résolvez la référence orpheline (utilisez
   `var.environment`).
3. Renommez les ressources en **snake_case** descriptif, sans répéter le type.
4. **Typez et décrivez** les quatre variables. `replica_count` doit être
   `number`.
5. **Typez et décrivez** les outputs. Marquez le jeton d'API `sensitive`, et
   déclarez `type = number` sur l'output des replicas.
6. Ajoutez un **`.gitignore`** qui exclut `.terraform/`, `terraform.tfstate*` et
   les `.tfvars`, mais **pas** `.terraform.lock.hcl` (attention au piège
   `.terraform*`).

Le style guide recommande aussi de **découper** `infra.tf` en `terraform.tf`,
`providers.tf`, `variables.tf`, `main.tf`, `outputs.tf` : faites-le, c'est la
bonne pratique. Le contrôle, lui, porte sur les invariants ci-dessus.

## 🔍 Validation

```bash
dsoxlab check write-code-style-guide
```

Dix tests lisant `terraform fmt -check`, `validate -json`, `show -json`,
`output -json`, des codes retour et le `.gitignore` : formatage, validité, les
deux ressources intactes, les noms en snake_case, les variables décrites, le
typage `number`, les outputs (sensibilité, type, description), le `.gitignore`,
et l'idempotence. Aucun ne parse vos `.tf`.
