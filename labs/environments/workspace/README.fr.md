# Un workspace isole un état, et rien d'autre

Un workspace Terraform donne à une **même** configuration plusieurs instances
d'**état**. C'est tout ce qu'il fait. Il ne change ni le backend, ni les
credentials, ni le répertoire de travail.

## Où vivent les états, et où vit la sélection

Sur un backend local, `default` garde son état à la racine, et chaque autre
workspace reçoit le sien sous `terraform.tfstate.d/` :

```text
terraform.tfstate                       <- default
terraform.tfstate.d/dev/terraform.tfstate
terraform.tfstate.d/prod/terraform.tfstate
```

Le workspace **sélectionné**, lui, n'est pas dans l'état : il est écrit dans
`.terraform/environment`, un fichier **local** et jamais partagé.

```bash
cat .terraform/environment
```

Deux personnes sur la même copie de travail peuvent donc être sur deux
workspaces **différents** sans le savoir.

## Dériver le nommage de `terraform.workspace`

C'est l'expression qui rend une configuration unique utilisable par plusieurs
environnements, sans y écrire aucun nom en dur :

```hcl
resource "local_file" "app" {
  count = terraform.workspace == "prod" ? 3 : 1

  filename = "${path.root}/sorties/app-${terraform.workspace}-${count.index}.conf"
  content  = "environnement ${terraform.workspace} instance ${count.index}\n"
}
```

Une **variable** ne ferait pas la même chose : elle garde la même valeur d'un
workspace à l'autre tant qu'on ne la surcharge pas à chaque commande.

## Supprimer un workspace ne détruit rien

C'est le piège qui coûte le plus cher. Terraform refuse tant que le workspace
suit des ressources :

```text
Error: Workspace is not empty

Workspace "bac-a-sable" is currently tracking the following resource instances:
  - local_file.app[0]
  - random_pet.temoin

Deleting this workspace would cause Terraform to lose track of any associated
remote objects, which would then require you to delete them manually outside
of Terraform.
```

L'option `-force` passe outre, et laisse des **orphelins** :

```text
Deleted workspace "bac-a-sable"!

WARNING: "bac-a-sable" was non-empty.
The resources managed by the deleted workspace may still exist,
but are no longer manageable by Terraform since the state has been deleted.
```

Mesuré : les trois fichiers produits sont **toujours** sur le disque après un
`-force`. L'ordre correct est **détruire**, puis supprimer.

## Le workspace `default` ne se supprime jamais

Deux messages différents, selon l'endroit d'où l'on tente :

```text
Workspace "default" is your active workspace.
You cannot delete the currently active workspace.
```

Et si l'on bascule ailleurs d'abord, comme le conseillent beaucoup de guides :

```text
Cannot delete the default workspace
```

Basculer ne débloque donc **rien** : `default` n'est pas supprimable, point.

## `TF_WORKSPACE`, et ses deux effets de bord

C'est le seul moyen de sélectionner un workspace **sans** changer la sélection
locale, ce qui en fait l'outil des chaînes d'intégration :

```bash
TF_WORKSPACE=prod terraform output
```

Mais tant qu'il est posé, deux commandes **refusent** de s'exécuter :

```text
The selected workspace is currently overridden using the TF_WORKSPACE
environment variable.
```

Et surtout, mesuré sur 1.15.4 : s'il désigne un workspace **inexistant**, une
simple commande le **crée**. Un `TF_WORKSPACE=prd terraform apply` ne proteste
pas, il fabrique un environnement fantôme et applique dedans.

## Deux options qui font gagner du temps

```bash
terraform workspace select -or-create recette
terraform workspace new -state=ancien.tfstate reprise
```

La première évite de tester l'existence avant de basculer. La seconde initialise
un workspace **à partir d'un état existant**, la manœuvre de sortie quand on
scinde un projet. Attention à son message, qui annonce
« You're now on a new, empty workspace » alors que l'état importé est bien là.

## À vous de jouer

```bash
dsoxlab run environments-workspace
dsoxlab check environments-workspace
dsoxlab hint environments-workspace
```

Il se joue **hors ligne**, avec les providers `local` et `random`.

Sous-objectif d'examen visé : **3c**.

Référence : [les workspaces Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/workspace/)
