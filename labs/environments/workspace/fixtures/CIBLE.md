# Un seul repertoire, trois etats qui ne se voient pas

Un workspace isole un **etat**, et rien d'autre : ni les droits, ni le backend,
ni le repertoire de travail. Ce lab vous fait piloter trois instances d'etat
depuis une seule configuration, sans jamais dupliquer un fichier.

## Ce que le repertoire contient deja

- `versions.tf`, `outputs.tf` : **complets**, a ne pas toucher.
- `main.tf` : troue par des `???`.
- `variables.tf` : une variable `nom_env`. Lisez son commentaire avant de vous
  en servir.
- `terraform.tfstate.d/bac-a-sable/` : un workspace **herite**, deja applique,
  dont le fichier `sorties/app-bac-a-sable-0.conf` est le seul contenu de
  `sorties/`.

## L'etat a atteindre

| Point | Attendu |
| --- | --- |
| 1 | Le repertoire connait exactement **trois** workspaces : `default`, `dev`, `prod`. `bac-a-sable` a disparu. |
| 2 | `default` ne suit **aucune** ressource. |
| 3 | `dev` suit **2** ressources et produit **1** fichier ; `prod` en suit **4** et produit **3** fichiers. |
| 4 | Chaque fichier porte le nom du workspace qui l'a cree, **sans** aucune valeur litterale `dev` ou `prod` dans la configuration. |
| 5 | Ni `dev` ni `prod` n'a de changement en attente. |
| 6 | `sorties/app-bac-a-sable-0.conf` n'existe **plus**. |
| 7 | Le workspace selectionne en fin de travail est `default`. |

## Le point 6 merite qu'on s'y arrete

Supprimer un workspace ne detruit **rien**. Terraform vous en avertit, et refuse
meme de le faire tant que le workspace suit des ressources :

```text
Error: Workspace is not empty

Workspace "bac-a-sable" is currently tracking the following resource instances:
  - local_file.app[0]
  - random_pet.temoin
```

L'option `-force` passe outre, et c'est exactement ce qu'il ne faut **pas**
faire ici : elle supprime l'etat en laissant les fichiers sur le disque, donc
plus rien ne les gere.

```text
WARNING: "bac-a-sable" was non-empty.
The resources managed by the deleted workspace may still exist,
but are no longer manageable by Terraform since the state has been deleted.
```

L'ordre correct est donc : **detruire**, puis supprimer.

## Deux commandes utiles, et un piege

`terraform workspace select -or-create <nom>` evite de tester l'existence avant
de basculer, ce qui est le motif employe en integration continue.

La variable d'environnement `TF_WORKSPACE` selectionne un workspace **sans**
changer la selection locale. Elle a deux effets de bord mesures :

- tant qu'elle est posee, `workspace select` et `workspace new` **refusent** de
  s'executer ;
- si elle designe un workspace **inexistant**, une simple commande le **cree**,
  au lieu d'echouer.

## Comment verifier

Le workspace courant se lit dans un fichier, pas dans une sortie humaine :

```bash
cat .terraform/environment
```

Et l'inventaire des workspaces se lit dans l'arborescence ecrite par Terraform :

```bash
ls terraform.tfstate.d/
terraform workspace list
```
