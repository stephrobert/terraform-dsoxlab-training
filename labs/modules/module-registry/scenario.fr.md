# Scénario : consommer un module du registre et maîtriser la version installée

**Sous-objectif d'examen visé : 4b (utiliser un module).**

Brancher un module public est trivial, savoir quelle version tourne réellement ne
l'est pas : le fichier de verrouillage ne couvre **que** les providers, et
« Terraform does not remember version selections for remote modules ».

## Capacité visée

Déduire l'adresse de registre d'un module depuis le nom de son dépôt, l'appeler
avec trois contraintes différentes en obtenant trois résolutions distinctes,
adresser un sous-répertoire d'un dépôt Git, puis prouver depuis les seuls
artefacts de Terraform quelle version a été **installée** et quelle contrainte a
été **écrite**.

## D'où part l'apprenant

**Prérequis réseau** : les `terraform init` doivent joindre
`registry.terraform.io` et `github.com`. Le module retenu,
`cloudposse/label/null`, ne déclare aucun provider et s'applique sans compte
cloud : il ne produit que des locales et des sorties.

`challenge/work` contient trois projets indépendants, aucun state.

- `projet-epingle/` : un `module "etiquette"` dont `source` et `version` valent
  `"???"`, plus un `local_file` déjà écrit qui consomme la sortie du module, et
  un `outputs.tf` correct. C'est le seul projet qui déclare un provider.
- `projet-souple/` : **deux** appels du même module, `etiquette` et
  `etiquette_patch`, tous deux troués. Le premier doit accepter toute la série
  `0.x`, le second rester dans les correctifs de la `0.24.1`.
- `projet-sous-module/` : un `module "exports"` dont le `source` doit viser le
  sous-répertoire `exports` du dépôt `cloudposse/terraform-null-label`, figé sur
  le tag `0.25.0`. Ce projet s'initialise seulement, il ne s'applique jamais.

Le commentaire de chaque fixture donne la consigne sans donner l'adresse : le
dépôt et la convention `terraform-<PROVIDER>-<NAME>` suffisent à reconstituer
`cloudposse/label/null`.

## L'état à atteindre

1. `projet-epingle` installe **exactement** la `0.24.1`, et son `modules.json`
   porte la clé `Version`, qu'aucun module local ne possède.
2. La contrainte écrite dans ce projet est une version **exacte**, lisible dans le
   JSON du plan sous `module_calls.etiquette.version_constraint`.
3. Le `.terraform.lock.hcl` de ce projet mentionne le provider `hashicorp/local`
   et **aucune** trace du module.
4. `projet-souple` ne produit **aucun** fichier de verrouillage : sa seule
   dépendance est un module de registre.
5. Son appel `etiquette` porte une contrainte **souple** et résout la `0.25.0`, la
   plus récente qui la satisfait, tout en restant sous la `1.0.0`.
6. Son appel `etiquette_patch` résout la `0.24.1` : deux versions du **même**
   module coexistent dans un seul `modules.json`, la résolution se faisant par
   **appel**.
7. `projet-sous-module` est initialisé avec un `source` dont le `//exports`
   précède le `?ref=0.25.0`, son `Dir` pointant vers le sous-répertoire, et son
   `modules.json` portant l'entrée chaînée `exports.this`.
8. Les deux projets appliqués exposent `atelier-nord`, `atelier-sud` et
   `atelier-sud-patch`, et ne proposent plus aucun changement.

## Comment on le prouve

Aucun test ne lit un `.tf` de l'apprenant ni ne parse une sortie humaine.

- Les trois `.terraform/modules/modules.json`, écrits par Terraform à
  l'installation, chargés en JSON et indexés par `Key` : les champs `Source`,
  `Version` et `Dir` portent les points 1, 5, 6 et 7. C'est la seule preuve
  possible de la version résolue, ce module ne déclarant aucune ressource, donc
  `terraform show -json` n'expose aucun `child_modules`.
- `plan -out` puis `show -json` du plan : `version_constraint` donne la contrainte
  **écrite**, distincte de la version résolue (points 2, 5 et 6).
- Le `.terraform.lock.hcl`, également produit par l'outil : présent avec le seul
  provider dans un cas (point 3), **absent** dans l'autre (point 4).
- `output -json` pour les trois étiquettes, et `plan -detailed-exitcode` à 0 pour
  la convergence (point 8).

Un `challenge/work` nu échoue partout (l'`init` s'arrête sur `Invalid version
constraint`), recopier la même contrainte dans les deux appels de
`projet-souple` échoue sur le seul point 6, et inverser `//` et `?ref=` fait
échouer l'`init` sur `invalid ref: "0.25.0//exports"`.
