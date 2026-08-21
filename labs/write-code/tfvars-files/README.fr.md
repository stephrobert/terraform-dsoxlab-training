# Fichiers tfvars : précédence et variable non déclarée

Un fichier **`.tfvars`** fournit des valeurs sans toucher au code. Deux choses
piègent, et ce lab les traite : l'**ordre de précédence** exact quand plusieurs
sources se contredisent, et le sort d'une **variable non déclarée**, qui n'échoue
pas de la même façon selon d'où elle vient. Ce tutoriel les montre sur un exemple
**jetable** ; le challenge vous fait corriger une faute de frappe silencieuse.

## Le chargement automatique et la précédence

Terraform charge **sans argument** : `terraform.tfvars`, `terraform.tfvars.json`,
et tout `*.auto.tfvars(.json)`. Quand plusieurs sources donnent la même variable,
l'ordre est fixe, du plus faible au plus fort :

| Rang | Source |
|---|---|
| 1 | le `default` du bloc `variable` |
| 2 | `TF_VAR_<nom>` |
| 3 | `terraform.tfvars` |
| 4 | **`terraform.tfvars.json`** |
| 5 | `*.auto.tfvars` (ordre lexical) |
| 6 | `-var` / `-var-file` et HCP Terraform |

Le point souvent raté : **`terraform.tfvars.json` est un niveau distinct
au-dessus de `terraform.tfvars`**. Si les deux fournissent la même variable, la
variante JSON gagne.

## Le piège : la variable non déclarée

Voici le manque le plus coûteux. Une valeur affectée à une variable **sans bloc
`variable` correspondant** ne se comporte **pas** de la même façon selon sa
source :

- dans un **fichier** `.tfvars` : un simple **avertissement**, le `plan`
  réussit ;
- via **`-var`** : une **erreur**, le `plan` échoue ;
- via **`TF_VAR_`** : **silencieusement ignorée**.

```hcl
# terraform.tfvars, avec une faute de frappe
env  = "prod"
zoen = "eu-west-3"   # "zoen" au lieu de "zone" : la vraie variable reste au defaut
```

```text
Warning: Value for undeclared variable
```

Le plan **réussit**, mais `zone` garde son défaut. On croit avoir changé une
valeur, il n'en est rien. C'est exactement le « faux diagnostic pendant un plan »
que ce sujet apprend à éviter : **lisez les avertissements**.

## À vous de jouer

Vous savez que `terraform.tfvars.json` bat `terraform.tfvars`, et qu'une variable
mal orthographiée dans un `.tfvars` ne fait qu'un warning qui laisse la vraie
variable à son défaut. Le challenge vous fait corriger une telle faute de frappe
et faire gagner un `.tfvars.json`, et les tests lisent les valeurs résolues.

```bash
dsoxlab run write-code-tfvars-files
dsoxlab check write-code-tfvars-files
dsoxlab hint write-code-tfvars-files
```

Sous-objectif d'examen visé : **3c** (fournir les valeurs des variables).

Référence : [Les fichiers tfvars en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fichiers-tfvars/)
