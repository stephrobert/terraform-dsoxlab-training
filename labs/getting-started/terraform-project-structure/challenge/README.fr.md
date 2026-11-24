# Découper un monolithe sans bouger le plan

## La situation

**Sous-objectif d'examen visé : 2e (déclarer et consommer variables et outputs, y compris la précédence des valeurs), avec 2a (valider la configuration) en appui.**

Terraform évalue tous les fichiers `.tf` d'un répertoire comme un document unique : le nom des fichiers et leur ordre n'ont aucun effet fonctionnel. Découper un monolithe doit donc produire exactement le même plan, et c'est cela qu'on prouve, pas la présence de fichiers bien nommés.

## Capacité visée

Réorganiser une configuration existante en fichiers thématiques et démontrer, par comparaison de deux plans JSON, que la configuration résolue est restée strictement identique. Savoir ensuite quelle source de valeur l'emporte quand plusieurs définissent la même variable, et que déclarer deux fois le même nom casse le module.

## D'où part l'apprenant

`challenge/work` contient un unique fichier `tout.tf` qui empile, dans le désordre :

- le bloc `terraform` avec `required_version` et `required_providers` pour `local`, `null` et `random` ;
- les blocs `provider` correspondants ;
- quatre blocs `variable`, dont trois avec un `default` ;
- un bloc `locals` ;
- une `random_pet`, une `null_resource` et un `local_file` qui écrit un rapport dans le répertoire de travail ;
- trois blocs `output` exposant la valeur effective des variables.

Aucun fichier de valeurs, aucun state, aucun plan enregistré. Un `.terraform.lock.hcl` et un `terraform init` déjà passés permettent de jouer le lab sans réseau. Les trois providers n'écrivent que dans le répertoire courant : ni VM, ni credential, ni infrastructure distante.

## L'état à atteindre

1. Un plan de référence est figé **avant** toute réorganisation, produit par `terraform plan -out` puis `terraform show -json`.
2. `tout.tf` a disparu, remplacé par `terraform.tf`, `providers.tf`, `variables.tf`, `locals.tf`, `main.tf` et `outputs.tf`. Aucun bloc n'est ajouté, supprimé ni modifié : seul leur emplacement change.
3. Chaque nom de variable, de local et d'output est déclaré **exactement une fois** dans l'ensemble du répertoire. `terraform validate` sort en succès.
4. Un plan régénéré après découpage, avec les mêmes valeurs d'entrée, est identique au plan de référence.
5. Un `terraform.tfvars` fixe deux variables, et un `env.auto.tfvars` en redéfinit une des deux : c'est la valeur du fichier `auto` qui est retenue.
6. Une variable d'environnement `TF_VAR_` vise une variable également présente dans `terraform.tfvars` : la valeur du fichier l'emporte, ce qui matérialise le rang réel de `TF_VAR_`, juste au-dessus du `default`.
7. La quatrième variable, sans `default` ni valeur en fichier, n'est fournie que par `-var` sur la ligne de commande et l'emporte sur toute autre source.
8. La configuration est appliquée, puis un second plan ne propose plus aucun changement.

## Comment on le prouve

Les tests ne lisent que de l'état structuré. Aucune assertion ne porte sur la sortie humaine de Terraform, et aucune ne se contente de constater qu'un fichier porte le bon nom.

- **Invariance du plan** : les listes `resource_changes` des deux plans JSON sont comparées adresse par adresse, action par action, et sur les valeurs de `change.after`, après neutralisation des champs volatils. Toute divergence fait échouer le lab.
- **Découpage réel** : le test lit le bloc `configuration` de `terraform show -json`, qui porte la position source de chaque bloc, et exige que les blocs `terraform`, `provider`, `variable`, `locals`, `resource` et `output` proviennent de fichiers distincts. La preuve porte sur la configuration résolue, jamais sur un `ls`.
- **Interdiction du doublon** : le test dépose un fichier `.tf` supplémentaire redéclarant une variable existante, vérifie que `terraform validate -json` retourne un diagnostic de sévérité `error`, puis retire le fichier et confirme le retour au vert.
- **Précédence des valeurs** : après `terraform apply`, `terraform output -json` expose la valeur effective de chaque variable. Le test vérifie la valeur attendue pour chaque source, y compris le cas où `TF_VAR_` est écrasée par `terraform.tfvars`, puis rejoue une variante avec `-var` et recompare `output -json`.
- **Convergence** : `terraform plan -detailed-exitcode` doit retourner **0**. Un code 2 signale un plan non vide et fait échouer le lab.

## 🎯 Challenge : découper sans que le plan bouge

### 📦 Le point de départ

`challenge/work` contient **un seul fichier**, `tout.tf`, qui empile dans le
désordre le bloc `terraform`, les providers, quatre variables, un `locals`, trois
ressources et quatre sorties.

Il contient aussi `reference/monolithe.tf.txt` : une **copie de référence**,
fournie et non modifiable, dont l'extension n'est pas `.tf` pour que Terraform ne
la charge pas. Les tests s'en servent pour reconstruire le plan d'origine.

### ✅ Objectif

1. **Découper** `tout.tf` en six fichiers : `terraform.tf`, `providers.tf`,
   `variables.tf`, `locals.tf`, `main.tf`, `outputs.tf`. Aucun bloc n'est
   ajouté, supprimé ni modifié : seul leur emplacement change.
2. **Faire disparaître `tout.tf`.** Découper, c'est **déplacer**.
3. **Poser les valeurs** : un `terraform.tfvars` qui fixe `projet` et
   `environnement`, et un `env.auto.tfvars` qui redéfinit `environnement`.
4. **Appliquer** avec `revision` fournie par `-var`, la variable étant déclarée
   sans `default`.

L'énoncé fixe aussi une variable d'environnement, et elle compte :

```bash
export TF_VAR_projet="depuis-env"
```

### 🧭 Les valeurs attendues, et pourquoi

| Sortie | Valeur | Qui gagne |
| --- | --- | --- |
| `projet_effectif` | `depuis-tfvars` | `terraform.tfvars` bat `TF_VAR_` |
| `environnement_effectif` | `depuis-auto` | un `*.auto.tfvars` bat `terraform.tfvars` |
| `region_effective` | `eu-ouest` | personne ne la pose : son `default` gagne |
| `revision_effective` | `depuis-ligne-de-commande` | `-var` bat tout le reste |

La première ligne est celle qui surprend : `TF_VAR_` vit juste au-dessus du
`default`, et **en dessous de tout fichier de valeurs**.

### ⚠️ Copier n'est pas découper

Si `tout.tf` reste à côté des six fichiers, chaque nom est déclaré deux fois et
Terraform refuse : `Duplicate variable declaration`. Un nom ne se déclare qu'une
fois par **répertoire**, quel que soit le fichier.

### 🔍 Validation

```bash
dsoxlab check getting-started-terraform-project-structure
```

Neuf tests. Aucun n'ouvre vos `.tf`.

La preuve centrale est l'**invariance** : les tests reconstruisent le plan du
monolithe depuis la copie de référence, et le comparent au vôtre, adresse par
adresse et valeur par valeur.

La preuve du découpage se fait par **ablation** : chaque fichier est retiré dans
une copie, et quelque chose doit casser. Si retirer `variables.tf` ne change
rien, les variables ne sont pas dedans.

Bloqué ? `dsoxlab hint getting-started-terraform-project-structure`.
