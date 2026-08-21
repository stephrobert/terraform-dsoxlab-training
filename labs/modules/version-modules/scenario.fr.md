# Scénario : publier trois versions d'un module, et les consommer

**Sous-objectif d'examen visé : 4c (refactorer et versionner un module).**

Un module Git n'est pas versionné parce qu'on a écrit `version` quelque part : il
l'est parce qu'une **référence** existe et qu'un consommateur pointe dessus. Deux
pièges suivent aussitôt : l'argument `version` est refusé hors registre, et un
**tag se déplace**, ce qui en fait une référence commode mais pas immuable.

## Capacité visée

Publier une version mineure puis une version majeure d'un module partagé, en
faisant correspondre le numéro à la nature du changement, puis faire consommer
**trois** révisions différentes du même module par trois configurations racines,
chacune avec la forme de référence qui convient à son besoin.

## D'où part l'apprenant

`challenge/work` fonctionne **hors ligne**, sans aucun provider, et contient :

- `modules-src/etiquette/` : le module en version `1.0.0`, trois fichiers, une
  variable requise `prefixe`, les sorties `etiquette` et `version_module`. Le
  dossier n'est **pas** encore un dépôt Git : l'initialiser est le premier geste.
- `modules-src/CHANGELOG.md` : une seule entrée, `1.0.0`, avec un commentaire
  indiquant les deux qui manquent.
- `fige/main.tf` : `source = "???"`, arguments corrects, doit rester sur la
  `1.0.0`.
- `stable/main.tf` : `source = "???"` **et** une ligne `version = "1.1.0"`
  parasite, héritée d'un copier-coller depuis un bloc de registre.
- `migre/main.tf` : `source = "???"` avec les arguments de la `1.0.0`, à adapter
  au renommage de la `2.0.0`.
- `CIBLE.md` : les trois versions à publier, ce que chaque projet doit consommer,
  et les deux règles à ne pas oublier. Aucune commande Git n'y figure.

## L'état à atteindre

1. `modules-src` est un dépôt Git portant trois tags annotés, `v1.0.0`, `v1.1.0`
   et `v2.0.0`, sur trois commits distincts.
2. Au tag `v1.1.0`, le module accepte une variable `suffixe` **facultative**
   (`default = ""`), `prefixe` reste déclarée, et `version_module` vaut `1.1.0` :
   une configuration écrite pour la `1.0.0` s'applique encore telle quelle.
3. Au tag `v2.0.0`, `prefixe` est **renommée** `nom_projet` et `version_module`
   vaut `2.0.0`. L'ancien nom a disparu, c'est un changement incompatible.
4. `fige/` consomme le module par le **SHA-1** du commit de la `1.0.0`, et expose
   `version_module = "1.0.0"`.
5. `stable/` consomme `?ref=v1.1.0`, **sans** argument `version`, et expose
   `etiquette = "atelier-nord"`.
6. `migre/` consomme `?ref=v2.0.0`, ses arguments adaptés au renommage, et expose
   `etiquette = "chantier"`.
7. Les trois projets sont appliqués, donc leurs sorties sont dans leur state.

## Comment on le prouve

Les tests ne lisent aucun `.tf` écrit par l'apprenant.

- Les trois `.terraform/modules/modules.json`, écrits par Terraform à
  l'installation : leur `Source` donne la référence réellement résolue, ce qui
  porte les points 4, 5 et 6. Un `?ref=` de 40 caractères hexadécimaux distingue
  le SHA-1 d'un nom de tag.
- L'absence de clé `Version` dans ces entrées : elle n'existe que pour un module
  de **registre**. Un `modules.json` présent prouve d'ailleurs que la ligne
  `version` parasite a été retirée, l'`init` échouant sinon sur `Invalid registry
  module source address`.
- `terraform output -json` dans chaque projet : `version_module` vient du module
  **résolu**, il ne peut pas être écrit depuis la racine (points 1 à 6).
- Le code **installé** sous `.terraform/modules/` : la `1.1.0` doit encore
  déclarer `prefixe` et déclarer `suffixe` **avec** un `default`, la `2.0.0` doit
  déclarer `nom_projet` et **plus** `prefixe` (points 2 et 3).

Un `challenge/work` nu échoue partout. Pointer `fige/` sur le tag `v1.0.0` au lieu
du SHA-1 ne fait tomber que le test d'immuabilité, et publier une `1.1.0` dont le
`suffixe` serait obligatoire ne fait tomber que celui de rétrocompatibilité.
