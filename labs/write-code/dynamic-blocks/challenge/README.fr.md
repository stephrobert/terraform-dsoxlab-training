# 🎯 Challenge : générer un cloud-init, et buter sur le mur

## Point de départ

`challenge/work` construit un document cloud-init avec
`data "cloudinit_config" "principal"`. `versions.tf`, `variables.tf` et
`outputs.tf` sont **complets, à ne pas modifier**. Tout se joue dans `main.tf`,
qui contient deux difficultés :

- un bloc `dynamic "part"` troué par des `???` (la collection, le nom de
  fichier, le contenu) ;
- un `dynamic "lifecycle"` **volontairement présent**. Ce n'est pas une faute de
  frappe à réparer telle quelle : c'est une impasse à comprendre.

Lancez `terraform validate` d'abord. Vous verrez des erreurs de syntaxe sur les
`???`, puis, une fois le `dynamic "part"` écrit, ce mur :
`Blocks of type "lifecycle" are not expected here.`

La variable `modules` est une map de trois entrées, dont une porte `actif =
false`.

## ✅ Objectif

1. **Compléter le `dynamic "part"`.** Il génère une partie par module **actif**,
   triée par clé. Le filtre `actif` va dans le `for_each`, **jamais** dans le
   `content`. Le `filename` dérive de la **clé** du module (`part.key`), pas d'un
   rang.

2. **Garder l'en-tête littéral.** La première partie, `#cloud-config`, ne varie
   jamais : elle reste un bloc `part` écrit à la main, hors du `dynamic`. Ne
   l'absorbez pas dans le bloc dynamique.

3. **Démonter le piège `lifecycle`.** Un bloc de méta-arguments ne se génère pas
   par `dynamic`. Remplacez le `dynamic "lifecycle"` par un bloc `lifecycle`
   **littéral** portant `create_before_destroy = true`.

Après votre `apply`, `terraform plan` ne doit plus rien proposer.

## 🧭 Ce qui prouve que ce n'est pas du littéral

La configuration doit **suivre la variable** :

- avec `-var 'modules={}'`, il reste exactement **une** partie, l'en-tête ;
- avec quatre modules actifs, **cinq** parties.

Des blocs écrits à la main ne peuvent pas satisfaire ces deux cas à la fois. Et
un `dynamic` qui aurait avalé l'en-tête tomberait à zéro sur le premier.

## 🔍 Validation

```bash
dsoxlab check write-code-dynamic-blocks
```

Huit tests. Ils décodent `terraform show -json` (la liste ordonnée `part` de la
data source), `output -json` et le plan JSON pour `local_file.rendu`. Aucun ne
lit vos `.tf` : c'est le nombre et l'ordre des parties générées qui prouvent le
bloc dynamique.
