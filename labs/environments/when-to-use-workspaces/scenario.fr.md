# Scénario : arbitrer entre workspaces et configurations séparées

**Sous-objectif d'examen visé : 3d.**

La doc officielle est nette : les workspaces conviennent aux variations légères d'une même infrastructure, mais pas quand les déploiements exigent des credentials ou des contrôles d'accès distincts, ni pour découper un système en composants. Ce lab fait porter la décision à l'apprenant, puis lui fait payer le prix de la découpe : deux configurations séparées ne se parlent plus toutes seules, il faut leur faire partager des données.

## Capacité visée

Reconnaître, sur une configuration donnée, laquelle des deux stratégies s'applique, puis découper la partie qui ne relève pas des workspaces en deux configurations racine à states distincts, et rebrancher la dépendance entre elles par `terraform_remote_state` sans dupliquer une seule valeur.

## D'où part l'apprenant

`challenge/work` contient trois répertoires :

1. `mono/` : la configuration à arbitrer, déjà initialisée et appliquée dans le workspace `default`. Elle mélange un socle réseau et une application, et conditionne des ressources sur `terraform.workspace`. Un commentaire en tête précise que la prod est gérée par une autre équipe, avec ses propres droits. Ce répertoire est en lecture, il ne doit plus être appliqué.
2. `socle/` et `app/` : deux squelettes de configurations racine. `socle/main.tf` déclare des ressources `random_pet` et `local_file` mais ses `output` sont troués par des `???`. `app/main.tf` est troué à l'endroit du bloc `data` et de la référence à la valeur venue du socle. Ni l'un ni l'autre n'est initialisé.
3. `bac-a-sable/` : le cas où les workspaces restent légitimes. Une `locals` porte une map indexée par nom de workspace, avec des tailles différentes selon l'environnement, et le `lookup` de repli est troué par des `???`. Rien n'est appliqué, aucun workspace autre que `default` n'existe.

## L'état à atteindre

1. `socle/` est appliqué, son state local contient au moins une ressource en `mode: managed`, et il expose deux outputs non vides : l'identifiant du socle et le CIDR du réseau.
2. `app/` est appliqué et son state contient une ressource en `mode: data` de type `terraform_remote_state`, pointant sur le state de `socle/`.
3. Un output de `app/` reprend, à l'identique, la valeur de l'output correspondant de `socle/` : la donnée traverse deux states sans avoir été recopiée en dur.
4. `socle/` et `app/` gèrent des ensembles de ressources disjoints : aucune adresse de ressource managée n'apparaît dans les deux states.
5. Ni `socle/` ni `app/` n'utilise de workspace : aucun répertoire `terraform.tfstate.d` n'y existe, la découpe se fait par configuration, pas par workspace.
6. `bac-a-sable/` possède deux workspaces nommés `dev` et `prod`, appliqués tous les deux, chacun avec son propre state.
7. Dans `bac-a-sable/`, l'attribut de taille de la ressource vaut la valeur `dev` sous le workspace `dev` et la valeur `prod` sous le workspace `prod` : la map indexée par `terraform.workspace` est réellement branchée.
8. Les quatre états (socle, app, bac-a-sable en `dev`, bac-a-sable en `prod`) sont stables : aucun changement en attente.

## Comment on le prouve

Les tests n'ouvrent jamais un fichier `.tf` de l'apprenant, ils interrogent l'état structuré.

- `terraform show -json` dans `socle/` puis dans `app/` : on parcourt `values.root_module.resources` et on filtre sur `mode`. Le point 1 exige au moins une entrée `mode: managed` dans `socle`, le point 2 exige une entrée `mode: data` de `type: terraform_remote_state` dans `app`. C'est la preuve directe du partage entre configurations, invisible autrement.
- `terraform output -json` dans les deux répertoires : le test compare les chaînes obtenues. L'égalité entre l'output de `app` et celui de `socle` prouve le point 3. Une valeur recopiée en dur casserait dès que le socle est réappliqué, ce que le test provoque en relançant `apply` sur `socle` avec une entrée modifiée puis en revérifiant l'égalité.
- Les jeux d'adresses (`address`) issus des deux `terraform show -json` sont comparés : leur intersection doit être vide pour le point 4.
- Le point 5 se vérifie sur le disque, via l'internal documenté : `terraform.tfstate.d` est le répertoire où le backend local range les states des workspaces non `default`. Sa présence dans `socle/` ou `app/` fait échouer le test.
- Pour les points 6 et 7, le test lit directement `bac-a-sable/terraform.tfstate.d/dev/terraform.tfstate` et `.../prod/terraform.tfstate`, qui sont du JSON, et compare l'attribut de taille de chaque côté. Deux states existants et deux valeurs différentes prouvent d'un coup que les workspaces sont créés et que la map est câblée.
- Le point 8 utilise `terraform plan -detailed-exitcode` dans chaque configuration, et dans `bac-a-sable/` après un `workspace select` de chaque workspace : le code de sortie attendu est `0`. Un `2` signale un travail laissé à mi-chemin.

Un `challenge/work` vide échoue dès le premier test : sans `apply`, il n'existe aucun state à lire, et la seule égalité d'outputs entre deux states distincts ne peut pas être obtenue par hasard.
