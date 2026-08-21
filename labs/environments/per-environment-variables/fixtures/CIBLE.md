# La valeur qui gagne, et comment le prouver

Une seule configuration sert trois environnements. Le code ne change pas, seules
les **valeurs** changent. Encore faut-il savoir laquelle de six sources
concurrentes finit dans le plan.

## L'echelle de precedence, du plus faible au plus fort

| Rang | Source | Chargement |
| --- | --- | --- |
| 1 | `default` du bloc `variable` | implicite |
| 2 | variable d'environnement `TF_VAR_<nom>` | implicite |
| 3 | `terraform.tfvars` | automatique |
| 4 | `terraform.tfvars.json` | automatique |
| 5 | `*.auto.tfvars`, en ordre **lexical** | automatique |
| 6 | `-var` et `-var-file` | explicite |

Deux points que la plupart des tableaux ratent, et qui sont notes ici :

- les variables d'environnement `TF_VAR_` existent, et elles **perdent** contre
  le moindre fichier de valeurs ;
- `-var` et `-var-file` sont au **meme** rang. Ce n'est pas une hierarchie qui
  les departage, c'est l'**ordre des arguments** sur la ligne de commande.

## Les valeurs attendues par environnement

| Environnement | `disk_size_gb` | `retention_jours` | Profil produit |
| --- | --- | --- | --- |
| `dev` | 4 | 7 | `profils/dev.json` |
| `staging` | 4 | 14 | `profils/staging.json` |
| `prod` | 8 | 90 | `profils/prod.json` |

`base_image` et `tags` sont **communs** : ils viennent du fichier auto charge et
ne se repetent dans aucun fichier d'environnement.

## Le travail

1. **Retablir le garde-fou.** `terraform plan -input=false`, sans aucune option,
   doit **echouer** sur `No value for required variable`. Aujourd'hui il
   reussit : une source implicite fournit une valeur d'environnement.
2. **Declarer les types** de `base_image` et de `tags`, laisses en `???`.
3. **Completer les blocs** de `main.tf` et de `outputs.tf`, eux aussi troues.
   `taille_octets` est la taille du volume convertie en **octets**.
4. **Corriger** `envs/staging.tfvars` : une de ses cles est mal orthographiee.
   Terraform le signale sans echouer, et la valeur reste au `default`. La cle se
   corrige, elle ne se contourne pas par un `default`.
5. **Completer** `envs/prod.tfvars`, incomplet.
6. **Appliquer** l'environnement `prod`.

## Comment verifier, sans se fier a l'ecran

La valeur retenue se lit dans la representation JSON du plan, jamais dans le
texte affiche :

```bash
terraform plan -out=tfplan -var-file=envs/prod.tfvars
terraform show -json tfplan | jq '.variables'
```

Et pour constater que l'ordre des options tranche :

```bash
terraform plan -var 'disk_size_gb=16' -var-file=envs/prod.tfvars   # retient 8
terraform plan -var-file=envs/prod.tfvars -var 'disk_size_gb=16'   # retient 16
```
