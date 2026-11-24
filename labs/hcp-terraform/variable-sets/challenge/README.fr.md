# La précédence HCP Terraform à 15 niveaux, simulée en local

## La situation

**Sous-objectif d'examen visé : 6b (workspaces HCP Terraform et leurs options
de configuration), objectif évalué en QCM uniquement.**

Quinze étages, et une inversion que presque personne ne voit : chez les variable
sets **priority**, le scope le plus **large** gagne, alors que chez les sets
**normaux** c'est le plus **étroit**. Ce lab fait construire la table complète en
HCL, puis la fait juger par Terraform sur des cas que l'apprenant ne verra pas
avant la correction. Aucun compte HCP Terraform n'est requis.

## Capacité visée

Classer n'importe quelle source de valeur HCP Terraform dans l'ordre officiel de
quinze niveaux, et prédire la valeur retenue quand plusieurs sources définissent
la même clé, y compris entre deux sets de scope et de propriétaire identiques.

## D'où part l'apprenant

`challenge/work` contient une configuration qui s'applique déjà, sans
infrastructure distante (providers `local` et `null`), `terraform init` passé :

- `VOCABULAIRE.md` : les quinze identifiants de source imposés, dans le désordre,
  des cinq `priority_*` à `auto_tfvars` et `terraform_tfvars`, en passant par
  `cli_var`, `tf_var_env`, `workspace`, les quatre `set_*` normaux et `set_global`.
- `variables.tf` et `main.tf`, à ne pas modifier : `variable "cas"` en
  `map(map(string))` associe pour chaque cas une source à sa valeur,
  `variable "duel_lexical"` oppose deux sets de scope et propriétaire identiques,
  une ressource `local_file` sérialise le résultat.
- `precedence.tf` troué : `local.ordre`, liste de quinze entrées dont onze valent
  `"???"`. Les quatre déjà posées (`cli_var`, `tf_var_env`, `workspace`,
  `terraform_tfvars`) sont des ancres, elles interdisent de deviner la table en la
  faisant tourner d'un cran.
- `resolution.tf` à écrire, qui doit parcourir `local.ordre` sans jamais nommer un
  cas en dur, et `qcm.tf` troué : cinq affirmations à trancher en booléen (prise
  d'effet d'un set, mode d'exécution local, case HCL, relecture d'une variable
  sensible, rang de `*.auto.tfvars` face à `terraform.tfvars`).
- `cas.auto.tfvars` : six cas d'entraînement. Les outputs `ordre_precedence`,
  `resolutions`, `gagnant_lexical` et `reponses` sont déclarés vides, à brancher.

## L'état à atteindre

1. `ordre_precedence` expose les quinze identifiants dans l'ordre officiel exact,
   du plus prioritaire au moins prioritaire.
2. `resolutions` porte, pour chaque cas, la source retenue **et** sa valeur.
3. Un cas sans aucune source renseignée résout sur la sentinelle `default_hcl`,
   jamais sur `null` ni sur une erreur de plan.
4. `gagnant_lexical` départage par points de code Unicode, pas par ordre
   d'apparition dans la map.
5. `reponses` porte les cinq booléens attendus, et l'`apply` est idempotent.

## Comment on le prouve

Les tests ne lisent jamais un `.tf` ni un `.tfvars` de l'apprenant.

- `terraform apply` puis `terraform output -json` : `ordre_precedence` est comparé
  position par position à la liste officielle, une seule inversion fait échouer
  l'assertion.
- Contrôle anti triche : un second plan avec `-var` qui **remplace intégralement**
  `cas` par huit cas générés par les tests, puis `terraform show -json tfplan`
  interrogé sur `.planned_values.outputs.resolutions.value`. Une résolution codée
  cas par cas donne alors des gagnants faux. Deux cas visent l'inversion :
  `priority_org_workspace_scoped` bat `priority_project_project_scoped`, et
  `set_project_project_scoped` bat `set_org_workspace_scoped`.
- Un troisième plan injecte un cas vide et exige `default_hcl`, un `-var` sur
  `duel_lexical` mêle majuscules et chiffres hors ordre d'insertion, et
  `terraform show -json` expose le `local_file` en `mode: managed` avant que
  `terraform plan -detailed-exitcode` sorte en code 0. Un `challenge/work` vide
  n'expose aucun output et échoue dès la première assertion.

## 🎯 Challenge : classer quinze sources, et tenir sur des cas inconnus

### 📦 Le point de départ

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

### ✅ Objectif

1. **La table complète**, du plus prioritaire au moins.
2. **La résolution** : pour chaque cas, la source retenue **et** sa valeur.
3. **Un cas sans aucune source** résout sur la sentinelle, jamais sur `null` ni
   sur une erreur de plan.
4. **Le duel lexical** : départager deux sets identiques par points de code.
5. **Les cinq affirmations**, en booléens.

### 🧭 L'inversion, et c'est tout le sujet

Chez les variable sets **normaux**, la portée la plus **étroite** gagne.
Chez les **prioritaires**, c'est la plus **large**.

> When a variable set is priority, the values take precedence over any variables
> with the same key set at a more specific scope.

Et deux autres surprises : les fichiers sont **en bas** de la table, et une map
HCL **n'a pas d'ordre** — c'est le nom qui départage, pas l'ordre d'écriture.

### ⚠️ Une résolution écrite cas par cas ne passera pas

Les six cas fournis se résolvent à la main. Les tests en génèrent **huit
autres**, que vous ne verrez pas, dont deux visent l'inversion et un est vide.

Parcourez `local.ordre`. Ne nommez aucun cas.

### 🔍 Validation

```bash
dsoxlab check hcp-terraform-variable-sets
```

Douze tests. La table est comparée **position par position**, et le message
nomme le rang fautif. Aucun test ne lit vos `.tf` ni vos `.tfvars`.

Bloqué ? `dsoxlab hint hcp-terraform-variable-sets`.
