# Ce qu'il faut réorganiser, et ce qu'il est interdit de changer

`projet/main.tf` porte **tout** : le bloc `terraform`, les providers, les
variables, les ressources et les sorties. Le découper est un exercice de style,
jusqu'au moment où le découpage change le **plan** sans que personne ne s'en
aperçoive.

## Le découpage attendu

Le *style guide* officiel nomme les fichiers, et ce ne sont pas ceux qu'on croit :

| Fichier | Ce qu'il contient |
| --- | --- |
| `terraform.tf` | **un seul** bloc `terraform`, avec `required_version` et `required_providers` |
| `providers.tf` | **tous** les blocs `provider` |
| `variables.tf` | tous les blocs `variable`, en **ordre alphabétique** |
| `outputs.tf` | tous les blocs `output`, en **ordre alphabétique** |
| `main.tf` | les `resource` et les `data source` restants |

Aucun de ces noms n'est imposé par Terraform : ce sont des **conventions**, et
c'est justement pour cela qu'il faut suivre celle qui est **publiée** plutôt que
la sienne.

## Ce qui ne doit pas bouger

Le plan. Pas « le plan devrait être le même », pas « `validate` passe » : le plan,
**comparé** à celui d'avant le découpage.

C'est le point que la plupart des articles ratent. `terraform validate` ne
regarde ni l'état, ni la valeur des arguments : « The `validate` command does not
check if argument values are valid for a specific provider, but it will verify
that they are the correct type. It does not evaluate any existing state. » Un bloc
perdu au copier-coller passe donc `validate` sans un mot.

## Le dépôt lui-même

Le projet doit devenir un dépôt Git dont le `.gitignore` **ignore** ce qui ne se
committe jamais, et **laisse passer** ce qui se committe toujours :

| Fichier | Versionné ? |
| --- | --- |
| `.terraform/`, `terraform.tfstate`, `*.tfstate.backup` | **non** |
| un plan enregistré par `terraform plan -out=tfplan` | **non**, et attention, il n'a **aucune extension** |
| `.terraform.lock.hcl` | **oui**, toujours |

## Le formatage

`terraform fmt -check` ne regarde que le **répertoire courant**. Sur une
arborescence, il lui faut `-recursive`, sans quoi un contrôle d'intégration reste
vert avec des sous-répertoires mal formatés.
