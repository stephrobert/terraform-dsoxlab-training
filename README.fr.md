# Formation Terraform : Associate & Professional 2026

**Langue :** [English](./README.md) · [Français](./README.fr.md)

[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/terraform-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/terraform-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/terraform-training.svg)](https://score.getplumber.io/github.com/stephrobert/terraform-training)
[![Licence : CC BY 4.0](https://img.shields.io/badge/Licence-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Formation **Terraform** pratique, pilotée par la CLI
[`dsoxlab`](https://github.com/stephrobert/dsoxlab). Ce dépôt est le **catalogue
de labs** du parcours Terraform de
[blog.stephane-robert.info](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/parcours/),
orienté vers les certifications **Terraform Associate (004)** et **Terraform
Authoring and Operations Professional**.

## Ce que c'est

`terraform-training` est un **dépôt de contenu**, pas une application. Il
fournit :

- des **labs guidés** dont l'énoncé décrit une situation, jamais un mode
  d'emploi ;
- des **challenges** sans pas-à-pas, pour éprouver l'autonomie ;
- des **capstones** alignés sur les six objectifs de l'examen Professional ;
- une **validation automatique** qui prouve l'état que la configuration calcule,
  pas qu'une commande a été tapée ;
- un **score** avec des indices à coût croissant.

La CLI `dsoxlab` est le point d'entrée unique : elle pose un lab, affiche
l'énoncé, valide, note et rapporte. Elle vit dans **son propre dépôt** et
s'installe **séparément**.

## Prérequis

- Python 3.11+ et [`uv`](https://docs.astral.sh/uv/)
- `git`
- **`terraform` (ou `tofu`) sur le PATH** : tous les labs.
- **`libvirtd` et le provider `dmacvicar/libvirt`** : section `first-infra`
  uniquement, qui provisionne de vraies ressources locales.
- **Docker et [Floci](https://blog.stephane-robert.info/docs/cloud/aws/floci/)**,
  émulateur AWS local sous licence MIT (`floci/floci:1.6.0`) : section `aws` et
  quelques labs qui visent AWS. Le provider `hashicorp/aws` pointe vers Floci par
  un bloc `endpoints` : zéro compte AWS, zéro facture. Les labs concernés
  déclarent Floci dans `runtime.services`, et dsoxlab le démarre tout seul.
- **Docker**, pour le lab `vault-secrets` : il démarre un serveur
  `hashicorp/vault:1.21` en mode développement, déclaré de la même façon.
- **Un jeton HCP Terraform** : **un seul lab sur 88 en exige un**, et il est
  optionnel. Sans jeton, ses tests se skippent au lieu d'échouer. Voir
  [`docs/hcp-token.fr.md`](./docs/hcp-token.fr.md).

Pas de VM, pas de `dsoxlab provision` : contrairement aux catalogues Ansible et
Linux, Terraform tourne sur la machine de l'apprenant. Tous les labs sont en
`runtime: shell`.

## Installation

`dsoxlab` est publiée sur [PyPI](https://pypi.org/project/dsoxlab/) et s'installe
comme un outil autonome :

```bash
# 1. Installer la CLI dsoxlab (outil externe, hors de ce dépôt)
uv tool install dsoxlab        # ou : pipx install dsoxlab

# 2. Cloner ce catalogue de labs
git clone https://github.com/stephrobert/terraform-training.git
cd terraform-training

# 3. Vérifier que le contrat est valide
dsoxlab validate-structure
```

### Votre premier lab, en cinq minutes

```bash
dsoxlab list-labs                                     # parcourir le catalogue
dsoxlab run       getting-started-terraform-workflow  # poser l'état de départ
dsoxlab challenge getting-started-terraform-workflow  # lire la mission
# ... vous travaillez dans challenge/work ...
dsoxlab check     getting-started-terraform-workflow  # valider et noter
```

`run` crée le répertoire de travail du lab et y copie les fixtures déclarées.
Tout se passe ensuite dans `challenge/work` : c'est le seul endroit que vous
modifiez, et `dsoxlab clean` le retire.

Bloqué ? `dsoxlab hint <id>` révèle un indice, dont le coût est déduit du score.

### Garder à jour

```bash
git pull                       # le catalogue
uv tool upgrade dsoxlab        # le moteur
```

Les deux évoluent séparément. Un lab qui échoue après une montée de version de
Terraform est un défaut du catalogue : ouvrez une issue, le formulaire arrive
prérempli par `dsoxlab support --issue`.

## Comment ça marche

### Le contrat déclaratif, à deux niveaux

Le catalogue est décrit par des données, pas par du code, ce qui laisse le
moteur `dsoxlab` agnostique du domaine :

- **`meta.yml`**, à la racine, déclare l'identité du dépôt et l'**ordre** des
  sections affichées par `list-labs` ;
- **`lab.yaml`**, par lab, déclare ses `skills`, son `level`, son `runtime`
  (type, fixtures, services), ses `distros`, son `doc_url` et un bloc
  `validation`. Un `lab.fr.yaml` surcharge le `title` et la `description` en
  français, et rien d'autre.

`dsoxlab validate-structure` contrôle tout le contrat : `meta.yml` bien formé,
chaque lab référencé présent avec un `lab.yaml` valide, chaque fichier de test et
de fixture déclaré réellement là, et chaque lien relatif d'un README qui mène
quelque part.

### Le cycle de vie d'un lab

```bash
dsoxlab list-labs              # parcourir le catalogue
dsoxlab show      <id>         # métadonnées et état d'un lab
dsoxlab run       <id>         # poser l'état de départ
dsoxlab challenge <id>         # lire la mission, sans pas-à-pas
dsoxlab hint      <id>         # révéler un indice (déduit du score)
dsoxlab check     <id>         # lancer les tests, calculer et enregistrer le score
dsoxlab clean     <id>         # retirer le répertoire de travail
dsoxlab progress               # avancement par section, score moyen
```

### Les runtimes

| Runtime | Ce que le lab demande |
|---|---|
| `shell` | un terminal et `terraform`. Les tests lisent l'état que votre configuration calcule, sur votre machine. |
| `shell` + `floci` | en plus, Docker : dsoxlab démarre l'émulateur AWS déclaré dans `runtime.services`, et l'arrête avec la session. |
| `shell` + compte HCP | un seul lab, optionnel, qui fait tourner un vrai run distant chez HCP Terraform. |

### Le modèle de validation

La validation **prouve l'état, elle ne fait pas confiance à l'apprenant**. Chaque
lab livre des tests `pytest` sous `challenge/tests/` qui interrogent
`terraform show -json` et `terraform output -json` : ce que la configuration
CALCULE, jamais ce qu'un fichier contient.

Et un lab s'éprouve **dans les deux sens** : les tests doivent échouer avant le
travail, et passer après. Un test vert avant le travail n'est pas un test, c'est
une hypothèse du setup. Le `conftest.py` racine rejoue la solution de référence
avant les tests en mode formateur, pour prouver que la solution elle-même est
juste ; `dsoxlab check` passe, lui, par le chemin de l'apprenant.

Les solutions de référence vivent sous `solution/`, **chiffrées par
ansible-vault** : une solution livrée en clair gâche le lab, et git la garde pour
toujours.

### Score, indices, avancement

`check` enregistre un score (tests réussis sur total, moins le coût des indices
révélés). Les indices sont **en base64** dans `challenge/hints.yaml`, pour qu'on
n'y accède pas en ouvrant le fichier, et leur coût croît avec leur précision.
L'historique vit dans une base SQLite **locale à ce dépôt**.

## Catalogue

Les labs vivent sous `labs/` et sont ordonnés par `meta.yml`. La table ci-dessous
est générée à partir des vrais `lab.yaml` : lancez
`python3 scripts/gen_catalog.py` pour la rafraîchir.

<!-- LABS:START -->
### Discover Terraform

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `getting-started-terraform-overview` | Prouver que Terraform a une mémoire | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/presentation-terraform/) |
| `getting-started-declarative-vs-imperative` | Prouver l'idempotence là où le script impératif diverge | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/declaratif-vs-imperatif/) |
| `getting-started-terraform-vs-opentofu` | Prouver la compatibilité Terraform / OpenTofu, et où elle s'arrête | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/terraform-vs-opentofu/) |
| `getting-started-install-terraform` | Contraindre la version de la CLI et verrouiller les providers | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/installer-terraform/) |
| `getting-started-cli-terraform` | Mettre d'accord fmt, validate et les outputs | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/cli-terraform/) |
| `getting-started-terraform-workflow` | Lire un plan avant de l'appliquer | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/workflow-terraform/) |
| `getting-started-providers-resources-data-sources` | Ce que Terraform gère, ce qu'il se contente de lire | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/providers-resources-data-sources/) |
| `getting-started-terraform-project-structure` | Découper un monolithe sans bouger le plan | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/structure-projet-terraform/) |

### First infrastructures

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `first-infra-first-infrastructure` | Première infrastructure : le cycle complet, prouvé | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/premiere-infrastructure/) |
| `first-infra-variables-outputs` | Variables, locals et l'ordre de précédence réel | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/variables-outputs/) |
| `first-infra-virtual-network` | La dépendance que Terraform ne peut pas deviner | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/reseau-virtuel/) |
| `first-infra-vm-libvirt` | Mise à jour en place ou remplacement : le lire dans le plan | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/vm-libvirt/) |
| `first-infra-ansible` | Produire un inventaire Ansible depuis le state | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/ansible/) |
| `first-infra-debug-apply` | Reprendre après un apply qui a échoué, sans refaire le travail | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/debug-apply/) |
| `first-infra-clean-destroy` | Détruire proprement, et les quatre choses que cela recouvre | l1 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/destroy-propre/) |

### Writing Terraform code

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `write-code-providers` | Source explicite et alias de provider | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/providers-terraform/) |
| `write-code-declare-resources` | Lire le cycle de vie d'une ressource dans le plan | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/declarer-ressources/) |
| `write-code-variables` | Variables, typage, validation et précédence | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/variables-terraform/) |
| `write-code-outputs` | Le secret que l'output ne cache pas | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/outputs-terraform/) |
| `write-code-locals` | Le local qui ne se calcule pas au plan | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/locals-terraform/) |
| `write-code-data-sources` | À quel moment Terraform lit-il une data source ? | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/data-sources/) |
| `write-code-expressions` | Ce que les expressions calculent vraiment | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/expressions-terraform/) |
| `write-code-functions` | Composer des valeurs avec les fonctions HCL | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fonctions-terraform/) |
| `write-code-provider-defined-functions` | Fonctions définies par les providers | l2 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/provider-defined-functions/) |
| `write-code-conditionals` | La configuration qui refuse les valeurs absurdes | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/conditions-terraform/) |
| `write-code-validation-check-preconditions` | Conditions personnalisées : precondition, postcondition et blocs check | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/custom-conditions/) |
| `write-code-count` | count indexe par position, et la position ment | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/count-terraform/) |
| `write-code-for-each` | Ajouter une instance sans detruire les autres | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/for-each-terraform/) |
| `write-code-for-loops` | Transformer un catalogue avec les expressions for | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/boucles-for-terraform/) |
| `write-code-dynamic-blocks` | Générer des blocs, et savoir ne pas le faire | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/blocs-dynamiques/) |
| `write-code-depends-on` | depends_on ne se pose que là où une référence ne peut aller | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/depends-on/) |
| `write-code-lifecycle` | Le bloc lifecycle décide de l'ordre, pas vous | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/lifecycle-terraform/) |
| `write-code-tfvars-files` | La faute de frappe qui ne casse rien | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fichiers-tfvars/) |
| `write-code-version-constraints` | Contraintes de version et lock file | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/version-constraints-terraform/) |
| `write-code-style-guide` | La configuration qui marche mais qu'aucune CI n'accepte | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/style-guide-terraform/) |
| `write-code-sensitive-data-sensitive-values` | Quand la sensibilité casse for_each | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/sensitive-terraform/) |
| `write-code-sensitive-data-ephemeral-values` | La valeur qui ne touche jamais le state | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/ephemeral-values/) |
| `write-code-sensitive-data-write-only-arguments` | Arguments write-only : un secret qui n'atterrit jamais dans le state | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/write-only-arguments/) |
| `write-code-sensitive-data-vault-secrets` | Lire des secrets depuis Vault | l2 | TF-PROFESSIONAL | shell + vault | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/vault-secrets/) |

### Terraform State

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `state-understand-state` | Reprendre un secret déjà en service, sans le régénérer | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/comprendre-state/) |
| `state-backends` | Migrer le state sans casser sa lignée | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/backends-terraform/) |
| `state-state-locking` | Verrouillage du state, ce qu'il bloque vraiment | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/verrouillage-state/) |
| `state-terraform-state-list` | terraform state list, l'adresse est l'identité | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-list/) |
| `state-terraform-state-show` | terraform state show, ce que la fiche cache | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-show/) |
| `state-terraform-state-mv` | terraform state mv et le bloc moved, refactorer sans détruire | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-mv/) |
| `state-terraform-state-rm` | terraform state rm et le bloc removed, cesser de gérer sans détruire | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-rm/) |
| `state-removed-block` | Le bloc removed : léguer une infrastructure sans la détruire | l2 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/bloc-removed/) |
| `state-backup-restore-state` | Restaurer un state amputé : choisir la bonne sauvegarde, prouver que rien n'a été recréé | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/sauvegarder-restaurer-state/) |
| `state-diagnose-state` | Diagnostiquer une dérive et adopter une orpheline, sans perdre sa valeur | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/diagnostiquer-state/) |

### Terraform Modules

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `modules-create-modules` | Un module réutilisable ne configure aucun provider | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/creation-modules/) |
| `modules-module-structure` | Refactorer un monolithe vers la structure standard | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/structure-module/) |
| `modules-module-variables-outputs` | L'interface d'un module est un contrat, pas seulement des types | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/variables-outputs-module/) |
| `modules-module-local` | Un module local se lit sur place, il ne s'installe pas | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/module-local/) |
| `modules-module-registry` | Un module de registre est téléchargé, versionné, et jamais verrouillé | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/module-registry/) |
| `modules-version-modules` | Publier et consommer des versions de module avec des tags Git | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/versionner-modules/) |
| `modules-test-module` | Prouver un module avec terraform test, mutations comprises | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/tester-module/) |
| `modules-module-best-practices` | Rendre un module composable, et le prouver depuis le JSON du plan | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/bonnes-pratiques-modules/) |
| `modules-module-anti-patterns` | Refactorer un projet copie-colle sans rien detruire | l2 | TF-ASSOCIATE · TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/anti-patterns-modules/) |

### Environments

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `environments-organize-terraform-repo` | Decouper une configuration monolithique, et prouver que le plan n'a pas bouge | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/organiser-repo-terraform/) |
| `environments-separate-environments` | Deux racines, deux etats, un seul module partage | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/separer-environnements/) |
| `environments-per-environment-variables` | Quelle valeur gagne, et comment le prouver | l3 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/variables-par-environnement/) |
| `environments-workspace` | Un seul repertoire, trois etats qui ne se voient pas | l3 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/workspace/) |
| `environments-when-to-use-workspaces` | Workspaces ou configurations separees, et ce que coute la decoupe | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/quand-utiliser-workspaces/) |
| `environments-monorepo-vs-repo-per-stack` | Decouper un monorepo en deux stacks qui se parlent | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/monorepo-vs-repo-par-stack/) |
| `environments-terraform-in-automation` | Exécuter Terraform en automation (CI/CD) | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/terraform-en-automation/) |

### Terraform on AWS (via Floci)

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `aws-provider-aws-first-ec2` | Provider AWS : authentification, endpoints et tags par defaut | l3 | TF-ASSOCIATE | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/provider-aws-premiere-ec2/) |
| `aws-sg-subnet-instance` | Security group : regles dediees, for_each et subnet deterministe | l3 | TF-ASSOCIATE | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/sg-subnet-instance/) |
| `aws-iam-role-policy-instance-profile` | Composer la chaîne IAM, et nommer ses deux policies correctement | l3 | TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/iam-role-policy-instance-profile/) |
| `aws-backend-s3-remote-state` | Un state distant, verrouille, et lu par une autre stack | l3 | TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/backend-s3-remote-state/) |
| `aws-launch-template-autoscaling` | Lire un remplacement dans le plan, avant qu'il n'arrive | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/launch-template-autoscaling/) |
| `aws-import-moved-drift` | Import, moved et dérive : les trois pièges qu'un tutoriel ne montre jamais | l3 | TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/import-moved-drift/) |

### HCP Terraform

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `hcp-terraform-hcp-terraform-overview` | Le workflow d'un run : joué en deux temps, puis qualifié | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/presentation-hcp-terraform/) |
| `hcp-terraform-hcp-workspaces` | Workspaces : un mot, deux sens, deux stratégies de rattachement | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/workspaces-hcp/) |
| `hcp-terraform-remote-runs` | Le flux qu'un run renvoie, et les trois façons de le lancer | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/remote-runs/) |
| `hcp-terraform-variable-sets` | Quinze niveaux de précédence, et une inversion | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/variable-sets/) |
| `hcp-terraform-shared-credentials` | Les identifiants ne vivent ni dans le code, ni dans le state | l3 | TF-PROFESSIONAL | shell + floci | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/credentials-partage/) |
| `hcp-terraform-projects-teams` | Les permissions s'additionnent, elles ne s'écrasent pas | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/projects-equipes/) |
| `hcp-terraform-policy-as-code` | Policy as code : qui bloque un run, et qui peut passer outre | l3 | TF-PROFESSIONAL | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/policy-as-code/) |
| `hcp-terraform-premier-run-distant` | Le premier run distant, pour de vrai (optionnel, demande un compte) | l3 | TF-PROFESSIONAL | shell + compte HCP | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/hcp-terraform/remote-runs/) |

### Associate Certification (004)

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `certifications-associate-essential-commands` | Les commandes que l'examen attend, faites plutôt que récitées | l4 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/associate/) |
| `certifications-associate-mock-004` | Associate 004 : examen blanc | l4 | TF-ASSOCIATE | shell | [guide](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/associate/) |

### Professional Certification (capstones by objective)

| Lab (id) | Titre | Niveau | Certif | Runtime | Guide compagnon |
|---|---|---|---|---|---|
| `certifications-professional-capstone1-resource-lifecycle` | Pro · Objectif 1 : cycle de vie, import et réconciliation de drift | l4 | TF-PROFESSIONAL | shell + floci | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone2-dynamic-config` | Pro · Objectif 2 : configuration dynamique et troubleshooting | l4 | TF-PROFESSIONAL | shell | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone3-collaborative-workflows` | Pro · Objectif 3 : workflows collaboratifs | l4 | TF-PROFESSIONAL | shell + floci | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone4-modules` | Pro · Objectif 4 : créer, maintenir et utiliser des modules | l4 | TF-PROFESSIONAL | shell | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone5-providers` | Pro · Objectif 5 : configurer et utiliser les providers | l4 | TF-PROFESSIONAL | shell + floci | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-capstone6-hcp` | Pro · Objectif 6 : HCP Terraform (QCM) | l4 | TF-PROFESSIONAL | shell | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |
| `certifications-professional-mock-pro` | Pro · Mock intégratif 4h | l4 | TF-PROFESSIONAL | shell | [guide](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review) |

_88 labs, table générée par `scripts/gen_catalog.py`._
<!-- LABS:END -->

## Contribuer et licence

Les contributions sont bienvenues : lisez
[CONTRIBUTING.fr.md](./CONTRIBUTING.fr.md), qui décrit l'anatomie réelle d'un lab
de ce dépôt et la règle d'or, un lab s'éprouve dans les deux sens. Le
[code de conduite](./CODE_OF_CONDUCT.fr.md) s'applique à tous les échanges, et
les vulnérabilités se signalent en privé : [SECURITY.fr.md](./SECURITY.fr.md).

### Licence

Ce contenu est publié sous [Creative Commons Attribution 4.0
International](./LICENSE) (CC BY 4.0). Vous pouvez le partager et l'adapter, y
compris commercialement, à condition de citer la source.
