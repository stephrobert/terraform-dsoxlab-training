# Scénario : un seul répertoire, trois états qui ne se voient pas

**Sous-objectif d'examen visé : 3c (workflow en automation).**

Un workspace n'isole que le state, jamais les droits ni le backend. Ce lab
traite les deux pièges que les guides oublient : `TF_WORKSPACE` bloque
`workspace select` et `workspace new` tant qu'il est posé, et `workspace delete
-force` supprime la trace des ressources sans supprimer les ressources.

## Capacité visée

Piloter plusieurs instances d'état dans un même répertoire de travail sans
jamais dupliquer la configuration : dériver le nommage et le dimensionnement de
`terraform.workspace`, sélectionner un workspace en mode non interactif, et
retirer proprement un workspace obsolète sans laisser d'objet orphelin.

## D'où part l'apprenant

`challenge/work` est déjà initialisé, avec les providers `local` et `random`
verrouillés par `.terraform.lock.hcl`, et contient :

- `main.tf` : un `random_pet` et une ressource `local_file` écrits aux trois
  quarts, dont le nom du fichier produit et le nombre d'instances sont troués par
  des `???`, à remplacer par une expression fondée sur `terraform.workspace`.
- `variables.tf` : une variable `nom_env` **avec** une valeur par défaut. C'est le
  piège, s'en servir fait passer `dev` et tombe sur `prod` comme sur le workspace
  témoin. Le défaut n'est pas un confort : mesuré sur 1.15.4, une variable racine
  sans `default` est exigée **même si aucune expression ne la référence**, ce qui
  ferait échouer toutes les commandes de l'apprenant sur
  `No value for required variable`.
- `outputs.tf` : trois outputs déjà écrits, `workspace_actif`, `fichier_produit`
  et `replicas`, qu'il ne faut pas modifier.
- `terraform.tfstate.d/bac-a-sable/` : un workspace hérité, déjà appliqué, dont
  le fichier `sorties/app-bac-a-sable-0.conf` est le seul contenu de `sorties/`.

## L'état à atteindre

1. Le répertoire connaît exactement trois workspaces : `default`, `dev` et
   `prod`. `bac-a-sable` a disparu.
2. `default` ne suit aucune ressource gérée : le state racine reste vide.
3. `dev` suit deux ressources gérées et produit un seul fichier ; `prod` en suit
   quatre et produit trois fichiers.
4. Chaque fichier produit porte le nom du workspace qui l'a créé, sans qu'aucune
   valeur littérale `dev` ou `prod` n'existe dans la configuration.
5. Ni `dev` ni `prod` n'a de changement en attente.
6. Le fichier `sorties/app-bac-a-sable-0.conf` n'existe plus : le workspace a été
   détruit avant d'être supprimé, pas supprimé avec `-force`.
7. Le workspace sélectionné en fin de travail est `default`.

## Comment on le prouve

Les tests n'ouvrent aucun `.tf`. Ils interrogent chaque workspace sans toucher à
la sélection de l'apprenant, en posant `TF_WORKSPACE` sur la commande :
`terraform show -json` rend les ressources en `mode: managed` par workspace, ce
qui prouve les points 2 et 3, et `terraform output -json` rend le nom de fichier
réellement calculé. L'inventaire des workspaces vient des sous-répertoires de
`terraform.tfstate.d`, écrits par Terraform, jamais d'une sortie humaine. Le
point 5 est un `terraform plan -detailed-exitcode` attendu en code 0 pour `dev`
et pour `prod`, et le point 7 se lit dans `.terraform/environment`.

Le point 6 est un constat d'absence sur le disque : un `-force` aurait laissé le
fichier hérité en place, faute de destroy. L'état du système sépare les deux
gestes là où la commande tapée ne le ferait pas.

Le point 4 est le seul qui exige une copie du dossier : les tests y font
`terraform workspace select -or-create controle` puis un apply, et attendent un
fichier nommé d'après `controle` avec une seule instance. Une valeur en dur ou
une `nom_env` fixée par un `.tfvars` produit ici le mauvais nom et tombe.
