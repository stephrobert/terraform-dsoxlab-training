# Six sources pour une variable, une seule gagne

Découper les valeurs par environnement dans des fichiers `.tfvars` est facile.
Savoir **laquelle** de six sources concurrentes finit dans le plan l'est beaucoup
moins, et c'est pourtant ce qui décide de ce que vous déployez.

## L'échelle, mesurée sur Terraform 1.15.4

Du plus faible au plus fort. Chaque marche a été vérifiée en opposant deux
sources et en lisant la valeur retenue dans le JSON du plan.

| Rang | Source | Chargement |
| --- | --- | --- |
| 1 | `default` du bloc `variable` | implicite |
| 2 | variable d'environnement `TF_VAR_<nom>` | implicite |
| 3 | `terraform.tfvars` | automatique |
| 4 | `terraform.tfvars.json` | automatique |
| 5 | `*.auto.tfvars`, en ordre **lexical** | automatique |
| 6 | `-var` et `-var-file` | explicite |

Deux marches manquent à presque tous les tableaux qu'on trouve en ligne.

## Piège n°1 : les variables d'environnement perdent contre un fichier

`TF_VAR_env_name` bat le `default`, mais **perd** contre le moindre
`terraform.tfvars` du dépôt. Une CI qui exporte ses valeurs par l'environnement
peut donc être silencieusement écrasée par un fichier commité.

```bash
export TF_VAR_valeur=ENVIRONNEMENT
terraform plan -out=tfplan
terraform show -json tfplan | jq -r '.variables.valeur.value'
```

```text
TFVARS
```

## Piège n°2 : `-var` ne gagne pas « toujours »

On lit souvent que `-var` surcharge **toute** autre source. C'est faux.
`-var` et `-var-file` sont au **même** rang, et c'est l'**ordre des arguments**
qui tranche :

```bash
terraform plan -var 'disk_size_gb=16' -var-file=envs/prod.tfvars   # retient 8
terraform plan -var-file=envs/prod.tfvars -var 'disk_size_gb=16'   # retient 16
```

Le même couple d'options, deux résultats. Rien ne le rend visible à l'écran :
seule la représentation JSON du plan le dit.

## L'ordre est lexical, pas alphabétique

Deux fichiers auto chargés se départagent sur les **octets** de leur nom, pas
sur un ordre alphabétique intuitif :

```text
9-x.auto.tfvars    valeur = "NEUF"
10-x.auto.tfvars   valeur = "DIX"
```

C'est **`NEUF`** qui gagne, parce que `"10-x"` précède `"9-x"` en lexical, donc
`9-x` est appliqué en dernier. Même effet entre `B.auto.tfvars` et
`a.auto.tfvars` : c'est `a` qui l'emporte, alors qu'un classement insensible à
la casse aurait désigné `B`.

## Une clé mal orthographiée ne casse rien, et c'est le problème

Trois comportements, selon l'endroit de la faute :

| Où | Ce que fait Terraform |
| --- | --- |
| `TF_VAR_inexistante` | **rien du tout**, en silence |
| dans un `.tfvars` | `Warning: Value for undeclared variable`, la variable reste à son `default` |
| avec `-var` | `Error: Value for undeclared variable`, code de retour **1** |

Un `disk_size_go` au lieu de `disk_size_gb` dans un fichier d'environnement
produit donc un plan **valide** avec la mauvaise taille.

## Le seul contrôle qui tranche

Ne lisez pas la valeur à l'écran, lisez celle que Terraform a **retenue** :

```bash
terraform plan -out=tfplan -var-file=envs/prod.tfvars
terraform show -json tfplan | jq '.variables'
```

```json
{
  "disk_size_gb": { "value": 8 },
  "env_name": { "value": "prod" },
  "retention_jours": { "value": 90 }
}
```

Une valeur passée par `-var` y figure en **chaîne** (`"16"`), même pour une
variable typée `number` : la représentation expose l'entrée brute, Terraform la
convertit ensuite selon le `type` déclaré.

## À vous de jouer

Le challenge vous remet une configuration qui sert trois environnements, avec un
`terraform.tfvars` qui neutralise son propre garde-fou, des types laissés en
`???` et une clé mal orthographiée.

```bash
dsoxlab run environments-per-environment-variables
dsoxlab check environments-per-environment-variables
dsoxlab hint environments-per-environment-variables
```

Il se joue **hors ligne**, avec les providers `local` et `random`.

Sous-objectif d'examen visé : **2e**.

Référence : [gérer les variables par environnement](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/variables-par-environnement/)
