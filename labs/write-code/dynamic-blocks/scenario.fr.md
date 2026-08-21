# Scénario : générer des blocs, et savoir ne pas le faire

**Sous-objectif d'examen visé : 2d.**

Un bloc `dynamic` fabrique des blocs imbriqués là où le schéma du provider en expose, et nulle part ailleurs : il ne peut pas produire un bloc de meta-arguments comme `lifecycle`, parce que Terraform doit traiter ces blocs avant qu'il soit sûr d'évaluer la moindre expression. Le lab traite ce mur, plus le réflexe qui coûte le plus cher en relecture : tout passer en `dynamic`, y compris ce qui ne varie jamais.

## Capacité visée

Produire un document cloud-init dont le nombre, l'ordre et le nom des parties viennent d'une variable, en gardant littéral le bloc qui ne varie pas, en filtrant dans le `for_each` et non dans le `content`, et en posant à la main le bloc `lifecycle` qu'aucun `dynamic` ne peut générer.

## D'où part l'apprenant

`challenge/work` contient une configuration ni initialisée ni appliquée, limitée aux providers `hashicorp/cloudinit` et `hashicorp/local` :

- `versions.tf` : complet, à ne pas toucher. `required_version = ">= 1.15.0"`, les deux providers épinglés.
- `variables.tf` : complet. `modules` est une `map(object({ contenu = string, actif = bool }))`, avec trois entrées par défaut dont une portant `actif = false`.
- `main.tf` : la data source `cloudinit_config.principal` existe. Sa première partie, l'en-tête `#cloud-config` commun à tous les hôtes, est déjà écrite en bloc `part` littéral. Le bloc `dynamic "part"` qui suit est troué par des `???` sur la collection itérée, sur le nom de fichier et sur le contenu.
- `main.tf` contient aussi `local_file.rendu`, qui écrit le rendu, et **un `dynamic "lifecycle"` volontairement présent** : la configuration ne passe pas `terraform validate` en l'état. Ce n'est pas une faute de frappe à corriger, c'est une impasse à comprendre.
- `outputs.tf` : `parties` et `nb_parties` sont amorcés, avec des `???` sur l'expression.

L'énoncé impose de lancer `terraform validate` avant toute modification. Le constat de départ est double, vérifié sur Terraform 1.15.4 : les `???` du bloc `dynamic "part"` lèvent d'abord des erreurs de syntaxe (`Invalid expression`), et une fois ce bloc écrit, le `dynamic "lifecycle"` bute sur `Blocks of type "lifecycle" are not expected here.` (le message nomme le **label** du bloc visé, jamais le mot `dynamic`). C'est ce mur, `lifecycle` ne se génère pas, sur lequel repose la moitié du lab.

## L'état à atteindre

1. La configuration valide : plus aucun `dynamic` posé sur un bloc de meta-arguments, `local_file.rendu` porte un bloc `lifecycle` écrit littéralement, avec `create_before_destroy = true`.
2. Après l'apply par défaut, `data.cloudinit_config.principal` porte exactement trois parties : l'en-tête littéral en premier, puis les deux modules actifs, triés par clé.
3. Le nom de fichier de chaque partie générée est dérivé de la **clé** de la map, pas d'un rang : la clé du module se retrouve telle quelle dans le `filename`.
4. Le module marqué `actif = false` n'a produit aucune partie : le filtre est dans le `for_each`, jamais dans le `content`.
5. Avec `-var 'modules={}'`, il reste exactement **une** partie, l'en-tête : la partie fixe n'a pas été absorbée dans le bloc dynamique.
6. Avec quatre modules actifs, cinq parties, dans l'ordre des clés : la même configuration suit la variable sans être retouchée.
7. `local_file.rendu` contient le rendu de la data source, et un changement de contenu se planifie en création puis destruction, jamais l'inverse.
8. Les sorties sont câblées : `parties` est la liste ordonnée des noms de fichiers, `nb_parties` leur nombre.
9. Un plan relancé juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les fichiers `.tf`.

- `terraform validate -json` : `valid` vaut `true`. Sur la version de départ, le même appel renvoie `false` (erreurs de syntaxe sur les `???`, puis `Blocks of type "lifecycle" are not expected here.` une fois le `dynamic "part"` complété).
- `terraform show -json` : dans `values.root_module.resources`, l'entrée `data.cloudinit_config.principal` est en `mode: "data"` et son `values.part` est une **liste ordonnée**. Les tests comparent sa longueur, la suite des `filename` et le `content_type` de chaque élément. C'est là, et nulle part ailleurs, que se lit le nombre de blocs réellement générés.
- Variantes : les tests recopient le workdir et son `.terraform` dans un répertoire temporaire, appliquent avec `-var 'modules={}'` puis avec quatre modules actifs, et relisent `show -json`. Une partie, puis cinq. Des blocs écrits en dur ne peuvent pas suivre ces deux valeurs à la fois, et un `dynamic` qui aurait avalé l'en-tête tombe à zéro sur le premier cas.
- Filtrage : la clé du module inactif n'apparaît dans aucun `filename`, et son contenu n'apparaît dans aucun `content`.
- Clé et non rang : chaque `filename` généré contient la clé de la map correspondante. Une itération qui n'exploiterait que `.value` ne peut pas produire ces noms.
- `lifecycle` : `terraform plan -out` avec un contenu de module modifié, puis `terraform show -json` du plan. `resource_changes` porte `local_file.rendu` avec `actions == ["create", "delete"]`. L'ordre inverse prouverait l'absence de `create_before_destroy`, et aucun bloc dynamique n'aurait pu poser ce bloc.
- `terraform output -json` : `parties` est une liste de chaînes de même longueur que `part`, `nb_parties` un nombre qui lui correspond.
- `terraform plan -detailed-exitcode` : code 0 juste après l'apply final.

Aucun de ces contrôles ne passe sur un `challenge/work` vide : le premier `show -json` n'y trouve aucune ressource.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/blocs-dynamiques/
