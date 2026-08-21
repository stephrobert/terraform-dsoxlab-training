# Scénario : Brancher plusieurs projets sur un module local partagé

**Sous-objectif d'examen visé : 4b (utiliser un module).**

Terraform ne considère un chemin comme local que s'il commence par `./` ou `../` :
tout le reste, chemin absolu compris, devient un paquet recopié dans le cache de
modules. Ce lab rend la différence visible sur `.terraform/modules/modules.json`.

## Capacité visée

Brancher plusieurs configurations racine indépendantes sur un même module local
partagé, puis prouver depuis les seuls artefacts générés par Terraform quel dossier
chaque appel lit vraiment et quels arguments l'appelant a vraiment passés.

## D'où part l'apprenant

`challenge/work` contient cinq dossiers, aucun `.terraform/`, aucun state.

- `modules-partages/artefact/` et `modules-partages/nom/` : deux modules complets,
  à ne pas modifier. `artefact` déclare les providers `local` et `random`, les
  variables `nom` (obligatoire) et `suffixe_aleatoire` (booléen, défaut `true`),
  une `local_file`, les sorties `chemin` et `configuration`, et appelle `nom` par
  `source = "../nom"`.
- `projet-dev/` : `module "artefact"` avec `source = "???"`, un argument parasite
  `version = "~> 1.0"`, `nom` déjà renseigné, des `outputs.tf` corrects.
- `projet-staging/` : `module "artefact"` entièrement troué, `source` et arguments
  en `???`, `outputs.tf` fournis.
- `projet-fige/` : `module "nom"` dont seul le `source` est troué, avec la
  consigne d'y démontrer le cas du chemin absolu. Il vise `modules-partages/nom`
  et non `artefact`, pour une raison mesurée : un chemin absolu transforme le
  module en **paquet**, et le `source = "../nom"` interne d'`artefact` sort
  alors de ce paquet. L'`init` échoue sur `Local module path escapes module
  package`, ce qui empêcherait toute observation.

## L'état à atteindre

1. `projet-dev` est initialisé et appliqué : son `modules.json` porte l'entrée
   `Key: "artefact"`, `Source` en `../`, `Dir` hors de `.terraform/`.
2. Le même fichier porte l'entrée chaînée `Key: "artefact.nom"`, `Source` valant
   `../nom` et `Dir` normalisé vers `modules-partages/nom`.
3. L'appel de module de `projet-dev` ne porte plus aucun argument `version`.
4. `projet-dev` ne passe pas `suffixe_aleatoire`, et la sortie du module vaut
   malgré tout `true` : la valeur par défaut du module s'applique.
5. `projet-staging` est appliqué depuis le même module, `nom` différent et
   `suffixe_aleatoire` à `false`, dans un state distinct à l'adresse identique.
6. `projet-fige` est initialisé, jamais appliqué, avec un `source` absolu : son
   `modules.json` porte alors un `Source` en `file://` et un `Dir` sous
   `.terraform/`. Vérifié sur 1.15.4 : ce `Dir` est un **lien symbolique** vers
   la source, pas une copie profonde, ce que le mot « copy » de la doc laisse
   pourtant entendre.
7. `projet-dev` et `projet-staging` sont convergés, aucun changement en attente.

## Comment on le prouve

Aucun test ne lit un `.tf` de l'apprenant ni ne parse une sortie humaine.

- Les trois `modules.json`, écrits par Terraform, chargés en JSON et indexés par
  `Key` : les points 1, 2 et 6 se lisent dans les couples `Source` et `Dir`.
- `plan -out` puis `show -json` du plan : `configuration.root_module.module_calls.artefact`
  donne le `source` retenu, l'absence de clé `version` (point 3) et les `expressions`
  fournies, dont l'absence de `suffixe_aleatoire` côté dev prouve le point 4.
- `show -json` de l'état : `values.root_module.child_modules[]` expose
  `address == "module.artefact"` en `mode: managed`, avec des valeurs différentes
  dans deux states séparés (point 5), et `output -json` confirme `true` puis `false`.
- `plan -detailed-exitcode` renvoie 0 sur dev et staging (point 7). Un dernier test
  modifie le module partagé, relance ce plan sans `init`, exige le code 2, puis
  restaure et réexige 0 : un module local relatif n'est jamais mis en cache.
