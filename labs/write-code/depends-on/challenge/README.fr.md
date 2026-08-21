# 🎯 Challenge : nettoyer les dépendances d'une livraison

## Point de départ

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

## ✅ Objectif

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

## 🧭 La règle qui gouverne tout

> Un bloc ne déclare **jamais** en `depends_on` une ressource qu'il **référence
> déjà** par ailleurs.

Le critère : la ressource utilise-t-elle une **donnée** de l'amont dans ses
arguments ? Si oui, une référence suffit. Si non, et seulement alors,
`depends_on`.

## 🔍 Validation

```bash
dsoxlab check write-code-depends-on
```

Huit tests. Ils décodent la section `configuration` du plan JSON, qui expose pour
chaque bloc ses `depends_on` et les `references` de ses expressions. Le test
central refuse tout `depends_on` qui double une référence, où qu'il soit posé.
Aucun test ne lit vos `.tf`.
