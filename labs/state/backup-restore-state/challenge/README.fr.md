# 🎯 Challenge : trois sauvegardes, une seule restaurable

## 📦 Le point de départ

`challenge/work` contient un projet **déjà appliqué**, et un incident déjà
survenu. Rien n'est à trous : **aucun `???`, aucun `.tf` à modifier**. Tout le
travail porte sur le state.

```bash
terraform init
terraform state list
```

Le state ne décrit plus que **deux** ressources, alors que `main.tf` en déclare
**trois** et que les **trois fichiers** de `artefacts/` sont bien là. Un
`terraform state rm` malencontreux est passé par là.

| Fichier | Ce que c'est |
| --- | --- |
| `main.tf` | la configuration, complète, **à ne pas toucher** |
| `artefacts/*.txt` | les trois objets réels, **intacts** |
| `terraform.tfstate` | le state amputé, celui qui ment |
| `reference/etat-initial.json` | copie figée de ce state, **à ne pas modifier** |
| `sauvegardes/sauvegarde-{1,2,3}.json` | trois candidates, sans étiquette |

**Il n'y a pas de filet.** Une commande de manipulation du state ne met pas à
jour `terraform.tfstate.backup` : elle dépose un fichier horodaté
`terraform.tfstate.<epoch>.backup`, et un nettoyage de répertoire les a tous
emportés. Ce qui reste tient dans `sauvegardes/`.

## ✅ Objectif

Remettre le state en accord avec l'infrastructure, **sans qu'aucun des trois
artefacts ne soit recréé**. Une seule des trois sauvegardes le permet.

## 📋 Ce qu'il faut obtenir

1. Un fichier `sauvegardes/avant-restauration.json`, produit **avant toute
   écriture**, contenant le state endommagé tel quel : le `lineage` du projet et
   ses **deux** ressources gérées.
2. Le state courant porte toujours le `lineage` d'origine du projet.
3. Le state courant décrit de nouveau les **trois** ressources `local_file`.
4. Le `serial` du state courant est **strictement supérieur** à celui de la
   sauvegarde restaurée.
5. `terraform plan -detailed-exitcode` sort en **code 0**.
6. Les trois fichiers de `artefacts/` ont leur contenu **et leur date de
   modification** d'origine : aucun n'a été réécrit.

## ⚠️ Le cœur du sujet

Deux champs départagent les trois candidates, et un troisième piège attend au
bout :

| Champ | Ce qu'il dit | Ce qu'il élimine |
| --- | --- | --- |
| `lineage` | l'identité de la lignée du state | une sauvegarde venue d'un **autre projet** |
| `serial` | le compteur d'écritures | une sauvegarde **périmée**, antérieure au dernier apply |

Terraform refuse d'emblée un `push` au `serial` plus ancien : c'est normal, une
restauration remet forcément un état antérieur. `-force` passe outre, **sans
confirmation, et sans revérifier le lineage**. À vous de le vérifier avant.

Le raccourci qui semble marcher, `terraform apply`, ne répare rien : il
**recrée** l'objet absent du state au lieu de réparer le state, et les tests
comparent les dates de modification.

## 🔍 Validation

`dsoxlab check state-backup-restore-state` prouve, par exécution :

- la photo préalable existe et décrit bien l'état **endommagé** ;
- le `lineage` du state courant est celui du projet, donc la sauvegarde
  étrangère n'a pas été poussée ;
- les trois ressources sont de nouveau gérées ;
- le `serial` courant est supérieur à celui de la sauvegarde, ce qu'un `push`
  produit et qu'une copie de fichier ne produit pas ;
- le plan ne propose plus rien, ce qui élimine la sauvegarde périmée ;
- les trois artefacts n'ont été ni supprimés, ni réécrits ;
- contrôle de comportement joué dans une copie : pousser la sauvegarde étrangère
  échoue bien sur `over unrelated state`.

Bloqué ? `dsoxlab hint state-backup-restore-state`.
