# Le jeton HCP Terraform : le créer, le poser, le vérifier

## D'abord : vous n'en avez pas besoin

**Aucun des sept labs `hcp-terraform` n'exige de compte ni de jeton.** Ils
s'arrêtent volontairement juste avant l'authentification, et c'est ce qui les
rend vérifiables partout :

```
Initializing HCP Terraform...

Error: Required token could not be found
```

Cette erreur est le but du lab `hcp-workspaces`, pas un échec : elle signifie que
votre bloc `cloud` a été accepté. Une configuration fautive n'arrive jamais
jusque-là.

Ce guide sert à **aller plus loin** : lancer de vrais runs distants, et jouer le
lab optionnel qui les met en œuvre.

## Créer le jeton

Le plus simple, et il écrit le fichier tout seul :

```bash
terraform login
```

La commande ouvre votre navigateur, vous demande de confirmer, puis écrit
`~/.terraform.d/credentials.tfrc.json`.

À la main, si vous préférez : sur `app.terraform.io`, votre avatar →
**User settings** → **Tokens** → *Create an API token*. Donnez-lui une
description qui dise d'où il vient, par exemple `poste-formation-terraform`, et
une expiration.

Trois portées existent, et elles ne se valent pas :

| Portée | Ce qu'elle permet | Pour quoi |
| --- | --- | --- |
| **utilisateur** | tout ce que vous pouvez faire | un poste de travail |
| **équipe** | ce que l'équipe peut faire | une chaîne d'intégration |
| **organisation** | gérer l'organisation, pas les workspaces | l'outillage d'administration |

Pour suivre cette formation, un jeton d'**utilisateur** convient.

## Où le poser, et lequel gagne

Trois emplacements, et **l'ordre compte** :

| Priorité | Emplacement | Portée |
| --- | --- | --- |
| 1 | `TF_TOKEN_app_terraform_io` | la session en cours |
| 2 | `TF_CLI_CONFIG_FILE`, s'il est défini | ce que ce fichier déclare |
| 3 | `~/.terraform.d/credentials.tfrc.json` | le poste |

La variable d'environnement se nomme `TF_TOKEN_` suivi du nom d'hôte, ses points
devenus des tirets bas : `app.terraform.io` donne `TF_TOKEN_app_terraform_io`.

```bash
export TF_TOKEN_app_terraform_io=<votre-jeton>
```

Et le fichier prend cette forme exacte :

```json
{
  "credentials": {
    "app.terraform.io": {
      "token": "<votre-jeton>"
    }
  }
}
```

### Le piège, mesuré

Le 2026-09-25, sur Terraform 1.16.1, sur une même configuration correcte :

| Ce qui est en place | Ce que Terraform fait |
| --- | --- |
| le fichier de credentials seul | il emploie le jeton du fichier |
| `TF_CLI_CONFIG_FILE` vers un fichier vide | `Required token could not be found` |
| ... **et** `TF_TOKEN_app_terraform_io` posée | il emploie le jeton de la variable |

Autrement dit : **une variable d'environnement passe devant le fichier**, même
quand on a pris soin de neutraliser ce dernier. C'est la cause la plus fréquente
d'un « j'ai pourtant mis à jour mon jeton, et rien ne change » : le jeton mis à
jour n'est pas celui que Terraform lit.

## Vérifier, plutôt que supposer

```bash
python3 scripts/diagnostic-jeton-hcp.py              # où est le jeton
python3 scripts/diagnostic-jeton-hcp.py --verifier   # + l'API dit s'il est accepté
```

Le script regarde tous les emplacements, **dit lequel l'emporte**, signale ceux
qui portent un jeton ignoré, et n'affiche jamais la valeur d'un jeton, seulement
sa longueur et une empreinte tronquée. Ses codes de retour : `0` un jeton est en
place, `1` aucun jeton, `2` un jeton refusé par l'API.

Un jeton refusé rend un `401 unauthorized`, et l'API répond exactement la même
chose quand aucun jeton n'est envoyé : ce code ne distingue pas « pas de jeton »
de « mauvais jeton », ce que le diagnostic tranche pour vous en regardant ce
qu'il a trouvé localement.

## Ce qu'il ne faut pas faire

- **Ne committez jamais un jeton.** Ni dans un `.tf`, ni dans un `.tfvars`, ni
  dans un fichier de credentials déposé dans un dépôt. Un méta-test de ce
  catalogue refuse tout fichier qui en porterait un.
- **Ne le passez pas en variable Terraform.** Le lab `shared-credentials` le
  mesure : une variable marquée `sensitive` n'est pas affichée, et sa valeur se
  retrouve **en clair dans le state**.
- **Ne le partagez pas**, y compris pour dépanner quelqu'un : un jeton
  d'utilisateur porte tous vos droits.

## Le révoquer

Sur `app.terraform.io`, **User settings** → **Tokens** → la corbeille. La
révocation est immédiate, et c'est le bon réflexe au moindre doute : en créer un
autre prend dix secondes.

```bash
terraform logout    # retire le jeton du fichier local, sans le révoquer côté HCP
```

Les deux gestes sont distincts, et il faut souvent les deux.
