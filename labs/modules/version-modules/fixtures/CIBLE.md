# Ce que la bibliothèque doit publier, et ce que chaque projet doit consommer

## Les trois versions à publier depuis `modules-src/`

Le dépôt n'est pas encore un dépôt Git : c'est votre premier geste. Chaque
version est un **commit** distinct, marqué par un **tag annoté**, et la sortie
`version_module` du module doit porter le numéro correspondant.

| Version | Changement à apporter au module | Nature |
| --- | --- | --- |
| `1.0.0` | aucun, c'est le code livré | version initiale |
| `1.1.0` | une variable `suffixe`, **facultative**, qui s'ajoute à l'étiquette derrière un tiret quand elle n'est pas vide | rétrocompatible |
| `2.0.0` | la variable `prefixe` est **renommée** `nom_projet` | incompatible |

Une configuration écrite pour la `1.0.0` doit continuer à s'appliquer telle
quelle sur la `1.1.0`. C'est ce qui distingue une version mineure d'une version
majeure.

## Ce que chaque projet doit consommer

| Projet | Référence à viser | Ce qu'il doit exposer |
| --- | --- | --- |
| `fige/` | la référence **immuable** du commit de la `1.0.0` | `version_module = "1.0.0"` |
| `stable/` | le **tag** `v1.1.0` | `version_module = "1.1.0"`, étiquette suffixée |
| `migre/` | le **tag** `v2.0.0` | `version_module = "2.0.0"` |

Un tag Git se **déplace** (`git tag -f`) : il nomme une version, il ne la fige
pas. Une seule forme de référence est réellement immuable, et c'est celle que
`fige/` doit employer.

## Deux règles à ne pas oublier

L'argument `version` **n'existe pas** hors registre. Un des trois projets en
porte un, hérité d'un copier-coller : l'`init` le refusera tant qu'il sera là.

Le dépôt est **local** : la source est donc une URL `git::file://`. Pour rester
portable, construisez-la avec `path.cwd` plutôt qu'en codant votre arborescence
en dur.
