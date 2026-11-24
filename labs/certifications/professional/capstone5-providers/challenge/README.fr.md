# Pro · Objectif 5, configurer et utiliser les providers

## La situation

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

## 🎯 Challenge : deux configurations d'un même provider

### 📦 Le point de départ

`challenge/work` contient un `main.tf` qui **ne s'applique pas**, et un
`CIBLE.md`. Floci fournit l'émulateur.

Trois choses manquent, et elles ne se manifestent pas au même moment :

1. **aucune contrainte de version** sur le provider ;
2. **le provider cherche une identité qui n'existe pas** : lancez un `plan` et
   lisez l'erreur, elle nomme ce qu'il n'a pas trouvé ;
3. **une exigence nouvelle** : les archives doivent vivre dans une seconde
   région, ce qu'une seule configuration ne peut pas faire.

Les deux premières se **diagnostiquent**. La troisième se **construit**.

### ✅ Objectif

1. **Une contrainte de version**, reflétée dans le fichier de verrouillage.
2. **Le provider par défaut** joint l'émulateur sans aller vérifier une identité
   inexistante : identifiants factices **non vides**, et les trois options qui
   le dispensent de chercher.
3. **Une seconde configuration**, aliasée, pour `us-east-1`. Elle porte ses
   propres options : rien ne s'hérite d'une configuration à l'autre.
4. **`aws_instance.archives`** créée par cette seconde configuration,
   `aws_instance.principal` par celle par défaut.

### 🧭 L'oubli qui ne se voit pas

Sans l'argument `provider`, une ressource utilise la configuration **par
défaut**. Elle est créée au mauvais endroit, et **rien ne le signale** : deux
instances se ressemblent, et l'état ne dit pas qui les a produites.

Le seul endroit qui le dit est le champ `provider_config_key` de la section
`configuration` du plan JSON.

### ⚠️ Le verrou ne se met pas à jour tout seul

`constraints` n'est écrit dans `.terraform.lock.hcl` qu'à la **création** de
l'entrée. Si vous ajoutez la contrainte après un premier `init`, supprimez le
verrou et relancez : ni `init`, ni `init -upgrade` ne le corrigent.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone5-providers
```

Six tests, dans un environnement **sans aucun identifiant AWS** : ni variable
`AWS_*`, ni `~/.aws`. C'est ce qui fait apparaître l'erreur à diagnostiquer, et
ce qui garantit que le lab mesure votre travail et non votre poste.

Une preuve sort de Terraform : Floci **isole par région**, donc chaque instance
doit être vue dans la sienne et absente de l'autre.

Bloqué ? `dsoxlab hint certifications-professional-capstone5-providers`.
