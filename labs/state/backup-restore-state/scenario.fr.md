# Scénario : restaurer un state amputé sans recréer l'infrastructure

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
