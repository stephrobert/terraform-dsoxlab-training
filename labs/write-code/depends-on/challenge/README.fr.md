# Depends_on ne se pose pas là où une référence suffit

## La situation

**Sous-objectif d'examen visé : 2d.**

Une référence d'attribut n'attend pas qu'une valeur soit connue : elle attend que la ressource amont ait fini d'être appliquée. Le piège traité ici est le `depends_on` de confort, posé en double d'une référence qui ordonnait déjà tout, pendant que la seule dépendance réellement cachée du projet, elle, manque et fait échouer l'apply.

## Capacité visée

Trancher, bloc par bloc, entre une dépendance déjà exprimée par une référence et une dépendance cachée : supprimer les `depends_on` redondants, remplacer un chemin écrit en dur par une référence, poser le seul `depends_on` que rien d'autre ne peut exprimer, et démontrer la forme du graphe obtenu dans le JSON de plan.

## D'où part l'apprenant

`challenge/work` ne contient ni state ni `.terraform` :

- `versions.tf` : complet, à ne pas toucher. `required_version = ">= 1.15.0"`, providers `hashicorp/local`, `hashicorp/null` et `hashicorp/random` épinglés.
- `variables.tf` : complet. `racine` (string, défaut `"livraison"`).
- `main.tf` : quatre blocs, dont deux sont piégés.
  - `random_pet.nom` : complet.
  - `local_file.manifeste` : écrit `${var.racine}/manifeste.json`, son `content` est un `jsonencode` qui référence `random_pet.nom.id`, et il porte en plus `depends_on = [random_pet.nom]`. La référence et le `depends_on` disent la même chose, l'un des deux est de trop.
  - `null_resource.socle` : complet, à ne pas toucher. Son `local-exec` crée le répertoire, attend deux secondes, puis y écrit le marqueur `.pret`. Il simule un service qui met du temps à être opérationnel et qui n'expose aucun attribut exploitable.
  - `null_resource.publication` : son `local-exec` vérifie la présence de `.pret` puis recopie le manifeste vers `publie.json`, avec les deux chemins écrits en dur, et sans aucun `depends_on`.
- `data.tf` : `data "local_file" "publie"` lit `${var.racine}/publie.json` par un chemin littéral, son `depends_on` est troué par `???`.
- `outputs.tf` : `nom_livraison` et `taille_publie` amorcés, valeurs trouées.

L'énoncé impose un `init` puis un `apply` avant toute modification. Le constat de départ est un double échec, vérifié sur Terraform 1.15.4 : d'abord des erreurs de syntaxe sur les `???` de `data.tf` et `outputs.tf` ; puis, une fois ces trous remplis mais tant que `publication` n'est pas reliée au socle, l'échec reproductible du provisioner, `Error running command 'test -f livraison/.pret && cp ...': exit status 1`. Terraform a lancé `publication` en parallèle du socle, parce qu'aucune ligne du code ne reliait les deux.

## L'état à atteindre

1. Un `apply` complet passe de bout en bout, et `livraison/publie.json` existe avec exactement le contenu de `livraison/manifeste.json`.
2. `local_file.manifeste` ne porte plus aucun `depends_on` : l'ordre avec `random_pet.nom` tient par la seule référence présente dans `content`.
3. La commande de `null_resource.publication` ne contient plus le chemin du manifeste en dur : elle interpole `local_file.manifeste.filename`. La dépendance devient implicite, comme la doc le recommande dès qu'une donnée de l'amont est utilisable.
4. `null_resource.publication` porte `depends_on = [null_resource.socle]`, et rien d'autre : c'est la seule dépendance du projet qu'aucune référence ne peut exprimer, puisque `null_resource` n'expose aucune donnée utile.
5. `data.local_file.publie` porte `depends_on = [null_resource.publication]` : ses arguments sont littéraux, rien n'indiquerait sans cela qu'il faut attendre la copie.
6. Les sorties sont câblées : `nom_livraison` vaut l'`id` du `random_pet`, `taille_publie` la longueur du contenu lu par la data source.
7. Aucun bloc de la configuration ne déclare en `depends_on` une ressource qu'il référence déjà par ailleurs.
8. Un `plan` juste après l'apply final ne propose plus rien.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les fichiers `.tf`.

- `terraform plan -out=tfplan` puis `terraform show -json tfplan`, section `configuration.root_module.resources` : `local_file.manifeste` n'a plus de clé `depends_on`, et ses `expressions.content.references` contiennent `random_pet.nom.id`. L'ordre est donc toujours garanti, sans le doublon.
- Même section, `null_resource.publication` : `depends_on == ["null_resource.socle"]` strictement, et `provisioners[0].expressions.command.references` contient `local_file.manifeste.filename`. Une seule dépendance explicite, une seule implicite, chacune sur le bon voisin.
- Même section, `data.local_file.publie` : `depends_on` contient `null_resource.publication`.
- Règle croisée sur toute la configuration : pour chaque bloc, l'intersection entre ses `depends_on` et les adresses citées dans ses `references` doit être vide. C'est le test qui refuse le `depends_on` de confort, quel que soit l'endroit où l'apprenant le pose.
- Plan à froid, après `destroy` : `resource_changes` contient une entrée d'adresse `data.local_file.publie`, `mode: "data"`, `actions: ["read"]`. La lecture a été repoussée à l'apply, ce qui prouve que le `depends_on` de la data source est réellement câblé et pas seulement écrit.
- État du système après apply : `livraison/publie.json` existe et son contenu est identique à celui de `livraison/manifeste.json`, ce qui n'est atteignable que si la copie a eu lieu après le socle et après l'écriture du manifeste.
- `terraform output -json` : `nom_livraison` est une chaîne non vide, `taille_publie` un entier strictement positif égal à la taille du manifeste.
- `terraform plan -detailed-exitcode` : code 0 juste après l'apply final.

Aucun de ces contrôles ne passe sur un répertoire vide, ni sur la configuration de départ, dont l'apply s'arrête en erreur.

Référence : https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/depends-on/

## 🎯 Challenge : nettoyer les dépendances d'une livraison

### Point de départ

`challenge/work` orchestre une petite livraison : un manifeste JSON, un service
qui prépare un répertoire, une copie, une lecture. `versions.tf` et
`variables.tf` sont **complets, à ne pas modifier**. Le reste mélange
volontairement les deux erreurs opposées : un `depends_on` **de trop**, et une
dépendance **cachée** qui manque.

Trois fichiers sont à corriger :

- `main.tf` : un `depends_on` redondant sur `local_file.manifeste`, et un
  `null_resource.publication` à relier au socle (chemin en dur, aucun lien).
- `data.tf` : le `depends_on` de la data source, troué par `???`.
- `outputs.tf` : deux valeurs trouées par `???`.

Lancez `terraform init` puis `terraform apply` : vous verrez d'abord des erreurs
de syntaxe sur les `???`, puis, une fois ceux-ci remplis, l'échec du provisioner
`Error running command '... exit status 1'` tant que `publication` n'est pas
reliée au socle.

### ✅ Objectif

1. **Retirer le `depends_on` redondant.** `local_file.manifeste` référence déjà
   `random_pet.nom.id` dans son `content` : l'ordre est garanti sans lui.

2. **Rendre une dépendance implicite.** La commande de `null_resource.publication`
   écrit le chemin du manifeste **en dur**. Remplacez-le par une référence à
   `local_file.manifeste.filename`.

3. **Poser le seul `depends_on` légitime.** `null_resource.publication` a besoin
   du marqueur `.pret` posé par `null_resource.socle`, qui n'expose aucune
   donnée. Aucune référence ne peut exprimer ce lien : ajoutez
   `depends_on = [null_resource.socle]`, et rien d'autre.

4. **Câbler la data source et les outputs.** `data.local_file.publie` lit un
   chemin littéral : posez son `depends_on` vers `null_resource.publication`.
   `nom_livraison` vaut l'`id` du `random_pet`, `taille_publie` la longueur du
   contenu lu.

Après votre `apply`, `terraform plan` ne doit plus rien proposer.

### 🧭 La règle qui gouverne tout

> Un bloc ne déclare **jamais** en `depends_on` une ressource qu'il **référence
> déjà** par ailleurs.

Le critère : la ressource utilise-t-elle une **donnée** de l'amont dans ses
arguments ? Si oui, une référence suffit. Si non, et seulement alors,
`depends_on`.

### 🔍 Validation

```bash
dsoxlab check write-code-depends-on
```

Huit tests. Ils décodent la section `configuration` du plan JSON, qui expose pour
chaque bloc ses `depends_on` et les `references` de ses expressions. Le test
central refuse tout `depends_on` qui double une référence, où qu'il soit posé.
Aucun test ne lit vos `.tf`.
