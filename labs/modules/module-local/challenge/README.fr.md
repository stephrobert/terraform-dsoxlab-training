# 🎯 Challenge : trois projets, un module partagé

## 📦 Le point de départ

`challenge/work` contient cinq dossiers et aucun state :

| Dossier | Ce que c'est |
| --- | --- |
| `modules-partages/artefact/` | module complet, **à ne pas modifier**. Il appelle lui-même `../nom` |
| `modules-partages/nom/` | module complet, **à ne pas modifier** |
| `projet-dev/` | `source` troué, **et un argument de trop** |
| `projet-staging/` | `source` et arguments entièrement troués |
| `projet-fige/` | `source` troué, à remplir en **chemin absolu** |

Chaque projet est une **racine indépendante** : son propre `init`, son propre
state, sa propre lecture du module partagé.

## ✅ Objectif

Brancher ces trois projets sur le module partagé, puis prouver **depuis les
artefacts de Terraform** quel dossier chaque appel lit vraiment.

## 📋 Ce qu'il faut obtenir

1. `projet-dev` initialisé et appliqué : son `modules.json` porte l'entrée
   `artefact` avec un `Source` en `../` et un `Dir` **hors** de `.terraform/`.
2. Le même fichier porte l'entrée chaînée `artefact.nom`, `Source` valant
   `../nom` et `Dir` normalisé vers `modules-partages/nom`.
3. L'appel de `projet-dev` ne porte **plus aucun** argument `version`.
4. `projet-dev` ne passe **pas** `suffixe_aleatoire`, et la sortie vaut quand
   même `true` : le défaut du module s'applique.
5. `projet-staging` appliqué depuis le **même** module, avec un autre `nom` et
   `suffixe_aleatoire = false`.
6. `projet-fige` **initialisé, jamais appliqué**, avec un `source` **absolu** :
   son `modules.json` porte alors un `Source` en `file://` et un `Dir` **sous**
   `.terraform/`.
7. `projet-dev` et `projet-staging` convergent : plus aucun changement en attente.

## ⚠️ Le cœur du sujet

Terraform ne devine pas qu'un chemin est local, il le **reconnaît à son
préfixe** : « A local path **must** begin with either `./` or `../` ». Tout le
reste part vers un autre mécanisme.

| Ce que vous écrivez | Ce que Terraform en fait |
| --- | --- |
| `../modules-partages/artefact` | **lu sur place**, `Dir` hors du cache |
| `modules-partages/artefact` | refusé : `Invalid module source address` |
| un chemin **absolu** | **paquet distant** : `Downloading file://...`, `Dir` sous `.terraform/` |

Deux conséquences pour `projet-fige`. Il vise `modules-partages/nom` et non
`artefact`, parce qu'un module transformé en paquet ne peut plus atteindre ce qui
est **au-dessus de lui** : le `../nom` interne d'`artefact` ferait échouer l'init
sur `Local module path escapes module package`. Et l'argument `version` de
`projet-dev` n'a de sens que pour un module de **registre** : sur une source
locale, l'init s'arrête sur `Invalid registry module source address`.

## 🔍 Validation

`dsoxlab check modules-module-local` prouve, par exécution :

- les trois `modules.json`, écrits par Terraform, sont lus en JSON et indexés par
  `Key` : les couples `Source` et `Dir` portent les points 1, 2 et 6 ;
- `.terraform/modules/` de `projet-dev` ne contient **que** `modules.json`,
  aucun dossier copié ;
- le JSON du plan montre l'absence de `version` et l'absence de
  `suffixe_aleatoire` dans l'appel de dev ;
- les deux projets appliqués exposent des configurations **différentes** depuis
  le **même** module ;
- un test modifie le module partagé dans une **copie**, replanifie **sans
  `init`**, et exige le code **2** : un module local relatif n'est jamais mis en
  cache ;
- `plan -detailed-exitcode` rend **0** sur dev et staging.

Aucun test ne lit vos fichiers `.tf`.

Bloqué ? `dsoxlab hint modules-module-local`.
