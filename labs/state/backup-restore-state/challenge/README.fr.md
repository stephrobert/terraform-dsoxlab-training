# Restaurer un state amputé sans recréer l'infrastructure

## La situation

**Sous-objectif d'examen visé : 1e, gérer le state, importer des ressources et réconcilier le drift.**

Une manipulation de state a mal tourné, le `terraform.tfstate.backup` a déjà été écrasé, et il reste trois sauvegardes candidates dont une seule est restaurable. Le piège traité est celui du garde-fou : `lineage` et `serial` décident si une restauration répare l'infrastructure ou la fait recréer.

## Capacité visée

Choisir la bonne sauvegarde de state parmi plusieurs candidates en comparant `lineage` et `serial`, la réinjecter avec `terraform state push` malgré le refus de Terraform, et prouver que l'infrastructure existante n'a pas été touchée. La capacité inclut le réflexe préalable : sauvegarder l'état endommagé avant d'y toucher, parce qu'un `push` ne se rejoue pas.

## D'où part l'apprenant

Le lab est de type `shell` : aucune machine virtuelle, aucun `dsoxlab provision`, tout se joue dans `challenge/work` avec le seul provider `hashicorp/local`.

Le répertoire contient une configuration complète et déjà appliquée : trois ressources `local_file` qui ont écrit trois fichiers dans `artefacts/`. Rien n'est à trous dans le code, il n'y a aucun `???` à remplir. Le travail porte entièrement sur le state, pas sur le HCL.

L'incident est déjà survenu. Le `terraform.tfstate` présent ne décrit plus que deux des trois ressources : la troisième a été retirée par un `terraform state rm` malencontreux, ce qui a incrémenté le `serial`. Les fichiers de `artefacts/` sont intacts sur le disque : c'est bien le state qui ment, pas l'infrastructure.

Le filet de sécurité a disparu, et c'est un enseignement du lab. Une commande de manipulation du state n'écrit **pas** dans `terraform.tfstate.backup` : elle dépose un fichier **horodaté**, `terraform.tfstate.<epoch>.backup`, vérifié sur 1.15.4. Ici, un nettoyage de répertoire a emporté tous les fichiers `*.backup`, qui sont gitignorés dans la plupart des dépôts. Il ne reste donc que le state amputé et les trois candidates du répertoire `sauvegardes/`.

Un répertoire `sauvegardes/` fournit trois fichiers JSON, sans indication de leur provenance :

- l'un est complet, porte le bon `lineage` et correspond au disque ;
- l'un porte le bon `lineage` mais date d'avant le dernier apply, avec le contenu périmé d'un des fichiers ;
- l'un semble complet mais provient d'un autre projet, son `lineage` est étranger.

## L'état à atteindre

1. Un fichier `sauvegardes/avant-restauration.json` existe, produit par `terraform state pull` avant toute écriture : une photo valide du state endommagé, avec le `lineage` du projet et seulement deux ressources en `mode: managed`.
2. Le state courant porte le `lineage` d'origine du projet. La sauvegarde au `lineage` étranger n'a donc pas été poussée, même de force.
3. Le state courant décrit à nouveau les trois ressources `local_file` en `mode: managed`, aux mêmes adresses qu'avant l'incident.
4. Le `serial` du state courant est strictement supérieur à celui de la sauvegarde restaurée, ce qui atteste d'un `push` réel et non d'un fichier recopié à la main par-dessus `terraform.tfstate`.
5. La configuration est convergée : plus aucun changement en attente.
6. Les trois fichiers de `artefacts/` portent toujours le même inode et le même contenu qu'au départ. Rien n'a été détruit ni recréé.

## Comment on le prouve

La validation n'ouvre jamais un fichier `.tf` et ne lit aucune sortie destinée à un humain. Elle interroge l'état structuré :

- `terraform show -json` sert de source unique pour les points 3 et 6 : les tests comptent les ressources en `mode: managed` de type `local_file` et vérifient que les trois adresses attendues sont présentes.
- `terraform state pull` est relu en JSON pour les points 2 et 4 : `lineage` comparé au lineage de référence consigné par le setup hors de `challenge/work`, et `serial` comparé à celui de la sauvegarde attendue. Un `serial` égal trahit une copie de fichier, un `lineage` différent trahit la mauvaise sauvegarde.
- `sauvegardes/avant-restauration.json` est parsé comme un state : `version`, `lineage`, et un décompte de deux ressources gérées. Un fichier vide, tronqué ou produit après la restauration échoue.
- `terraform plan -detailed-exitcode` doit renvoyer 0 pour le point 5. C'est ce test qui élimine la sauvegarde périmée : la restaurer laisse un écart entre le state et le contenu réel d'un fichier, et le code retour vaut alors 2.
- Les inodes et les empreintes des trois fichiers de `artefacts/` sont comparés aux valeurs relevées par le setup. Une recréation, même à contenu identique, change l'inode et fait tomber le test.

Un `challenge/work` laissé en l'état ne passe aucune de ces preuves : sans restauration, `terraform show -json` ne rend que deux ressources et le plan sort en code 2.

## 🎯 Challenge : trois sauvegardes, une seule restaurable

### 📦 Le point de départ

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

### ✅ Objectif

Remettre le state en accord avec l'infrastructure, **sans qu'aucun des trois
artefacts ne soit recréé**. Une seule des trois sauvegardes le permet.

### 📋 Ce qu'il faut obtenir

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

### ⚠️ Le cœur du sujet

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

### 🔍 Validation

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
