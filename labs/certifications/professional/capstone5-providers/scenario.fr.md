# Scénario : Pro · Objectif 5, configurer et utiliser les providers

**Objectif d'examen visé : 5** (5a architecture à plugins, 5b configuration avec
aliasing, versioning, sourcing et montées de version, 5c authentification,
5d diagnostic des erreurs de provider).

## Capacité visée

Faire cohabiter **plusieurs instances d'un même provider** dans une seule
configuration, maîtriser la contrainte de version et le fichier de verrouillage,
et **diagnostiquer une erreur de provider** au lieu de la subir.

## D'où part l'apprenant

Floci tourne en local. Dans `challenge/work`, une configuration ne déclare
qu'**un seul** provider `aws` visant l'émulateur, et une exigence nouvelle
tombe : certaines ressources doivent être créées via une **seconde
configuration de provider** (autre région, autres réglages).

La configuration comporte en outre deux problèmes volontaires : une contrainte
de version absente, et une **erreur d'authentification** provoquée par des
options manquantes sur le provider (le diagnostic exact fait partie de
l'exercice).

## L'état à atteindre

1. Deux configurations du provider `aws` coexistent, l'une par défaut et l'autre
   **aliasée**, et chaque ressource est explicitement rattachée à la bonne.
2. La version du provider est **contrainte** dans `required_providers`, et le
   fichier de verrouillage reflète cette contrainte.
3. L'erreur d'authentification est corrigée : le provider vise Floci avec les
   options qui désactivent les vérifications d'identité inutiles en local, et
   des identifiants factices non vides.
4. `terraform init` puis `apply` aboutissent, et les ressources sont bien créées
   côté Floci.

## Comment on le prouve

- Le state montre que les ressources ont été créées via **deux configurations de
  provider distinctes** : chaque ressource référence l'instance attendue.
- L'AWS CLI pointée sur Floci retrouve les ressources créées par chacune.
- `terraform init` réussit avec la contrainte de version, et le fichier de
  verrouillage contient bien le provider contraint.
- Un test vérifie que l'erreur initiale ne se reproduit plus : la configuration
  part d'un état qui échouait, et finit par un `apply` vert.
- Idempotence et destroy propre.
