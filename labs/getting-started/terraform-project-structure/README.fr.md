# Découper un monolithe sans bouger le plan

Terraform évalue **tous** les fichiers `.tf` d'un répertoire comme un document
unique. Le nom des fichiers et leur ordre n'ont aucun effet fonctionnel : ce sont
des conventions de lecture, pas des instructions.

Conséquence directe, et c'est tout le lab : découper un monolithe doit produire
**exactement le même plan**. Ce n'est pas la présence de fichiers bien nommés
qu'on prouve, c'est l'invariance.

## Le découpage conventionnel

| Fichier | Ce qu'il porte |
| --- | --- |
| `terraform.tf` | le bloc `terraform`, versions et providers requis |
| `providers.tf` | les configurations de providers |
| `variables.tf` | les entrées |
| `locals.tf` | les valeurs calculées |
| `main.tf` | les ressources |
| `outputs.tf` | les sorties |

Rien n'oblige à ces noms. Ils valent parce que toute l'équipe sait où regarder.

## Découper, c'est déplacer

Copier au lieu de déplacer déclare chaque nom **deux fois**, et Terraform
refuse :

```text
Error: Duplicate variable declaration
Error: Duplicate resource "local_file" configuration
```

Un nom ne se déclare qu'une fois par **répertoire**, quel que soit le fichier
qui le porte. C'est la même règle qui fait que l'ordre des fichiers n'a pas
d'importance : il n'y a qu'un seul espace de noms.

## La seule preuve qui vaille : comparer deux plans

```bash
terraform plan -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | {address, actions: .change.actions}'
```

Un fichier bien nommé ne prouve rien. Deux plans identiques, si.

Le lab reconstruit le plan du monolithe depuis une copie de référence fournie,
plutôt que de faire confiance à un plan que vous auriez figé : rien n'obligerait
ce dernier à avoir été pris **avant** le découpage.

## Ce que `show -json` ne dit pas

Mesure faite en écrivant ce lab, et elle a changé sa conception : **le plan JSON
n'expose aucune position source**. Ni `configuration.root_module.resources`, ni
les variables ne disent de quel fichier elles viennent.

Prouver « les variables sont dans `variables.tf` » sans ouvrir un `.tf` demande
donc autre chose : l'**ablation**. Retirer le fichier dans une copie, et
constater ce qui casse. Sans `variables.tf`, `validate` refuse. Sans `main.tf`,
le plan ne porte plus aucune ressource.

C'est une preuve qui porte sur le comportement, pas sur le texte.

## La précédence, et la marche que tout le monde place trop haut

Le lab fait poser la même variable par plusieurs sources à la fois :

```text
default  <  TF_VAR_  <  terraform.tfvars  <  *.auto.tfvars  <  -var
```

La marche décisive est la deuxième : un simple fichier de valeurs **bat** la
variable d'environnement. `TF_VAR_` vit juste au-dessus du `default`, et en
dessous de **tout** fichier.

La plus discrète est la troisième : un `*.auto.tfvars` est chargé
automatiquement, après `terraform.tfvars`. Son nom ne le dit pas, aucune commande
ne le mentionne, et le collègue qui en dépose un change le comportement de tous.

## À vous de jouer

```bash
dsoxlab run getting-started-terraform-project-structure
dsoxlab check getting-started-terraform-project-structure
dsoxlab hint getting-started-terraform-project-structure
```

Il se joue **hors ligne**, sur `local`, `null` et `random`.

Neuf tests. Trois d'entre eux portent une garde qui refuse de mesurer tant que
le monolithe est en place : sans elle, ils étaient verts avant tout travail,
puisque le monolithe produit déjà un plan identique à lui-même.

Sous-objectif d'examen visé : **2e**, avec **2a** en appui.

Référence : [structurer un projet Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/structure-projet-terraform/)
