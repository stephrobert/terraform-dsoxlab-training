# Contribuer à terraform-training

**Language:** [English](./CONTRIBUTING.md) · [Français](./CONTRIBUTING.fr.md)

Ce dépôt est un **catalogue de labs** consommé par la CLI
[`dsoxlab`](https://github.com/stephrobert/dsoxlab). Les contributions sont de
nouveaux labs, des correctifs et des traductions. La CLI vit dans son propre
dépôt : n'ajoutez pas de code moteur ici.

## Mise en place

```bash
uv tool install dsoxlab        # la CLI (outil externe)
git clone https://github.com/stephrobert/terraform-training.git
cd terraform-training
dsoxlab validate-structure     # vérifier le contrat
```

Pas de VM, pas de `dsoxlab provision` : contrairement aux catalogues Ansible et
Linux, Terraform tourne sur la machine de l'apprenant. Tous les labs sont en
`runtime: shell`.

## La règle d'or : un lab s'éprouve dans les deux sens

Un test qui passe ne prouve rien tant qu'on n'a pas vu **échouer** ce qui doit
échouer. Avant de commiter un lab :

```bash
dsoxlab run   <id>    # l'état initial est posé
dsoxlab check <id>    # DOIT échouer : le travail n'est pas fait
# puis la solution de référence
dsoxlab check <id>    # DOIT passer : 100/100
```

Un lab dont les tests passent **avant** le travail ne mesure rien. C'est le
défaut le plus coûteux du domaine, et il ne se voit qu'en regardant.

Demandez-vous, pour chaque test : **serait-il vert si l'apprenant ne faisait
rien ?** Si oui, ce n'est pas un test, c'est une hypothèse du setup. La
correction consiste à fusionner cette moitié dans le test final, où elle ne peut
être atteinte qu'après le travail.

## Ce que les tests doivent lire

L'état que la configuration **calcule**, jamais ce qu'un fichier contient :

```python
# NON : on relit ce que l'apprenant a écrit
assert "aws_instance" in open("main.tf").read()

# OUI : on lit ce que Terraform a produit
etat = show_json(WORKDIR)
assert [r["address"] for r in ressources(etat)] == ["aws_instance.web"]
```

`terraform output -json` et `terraform show -json` sont les deux portes. Lire un
`.tf` est un dernier recours, et il se justifie dans le test : certains faits
(un provider qui porte ses identifiants, un bloc `cloud` qu'on ne peut pas
initialiser sans compte) ne laissent de trace dans aucun état.

## Anatomie d'un lab

```text
labs/<section>/<lab>/
├── lab.yaml            # le contrat (id, level, runtime, fixtures, validation…)
├── lab.fr.yaml         # surcharge FR du title/description UNIQUEMENT
├── README.md / README.fr.md        # la leçon
├── scenario.md / scenario.fr.md    # la situation, l'état à atteindre, la preuve
├── fixtures/           # le matériel de départ, copié dans challenge/work
└── challenge/
    ├── README.md / README.fr.md    # la mission, sans pas-à-pas
    ├── hints.yaml                  # indices en base64, trois paliers de coût
    └── tests/test_functional.py    # la preuve
solution/<section>/<lab>/           # solution de référence, chiffrée par ansible-vault
```

Il n'y a ici ni `setup.yaml` ni `cleanup.yaml` : `runtime.fixtures` déclare ce
qui est copié, et `dsoxlab clean` retire le répertoire de travail. Un lab qui a
besoin d'un service (la section AWS utilise l'émulateur Floci) le déclare dans
`runtime.services`, et dsoxlab le démarre.

## Proposer un lab

- **Partir d'une capacité, pas d'un guide.** Décrivez quelque chose de
  démontrable (« importer une ressource existante et réconcilier une dérive sans
  la recréer »), ouvrez une issue, et calez le périmètre avant d'écrire.
- **Faites pointer `doc_url` vers le vrai guide** que le lab fait pratiquer. Un
  lab sans leçon jumelée enseigne au lieu d'éprouver, ce qui est le rôle du site.
- **Employez les versions courantes.** Épinglez-les, et datez la mesure en
  commentaire : un catalogue qui enseigne un argument déprécié est pire qu'un
  catalogue qui se tait.

## Vérifications locales avant d'ouvrir une PR

```bash
dsoxlab validate-structure        # le contrat meta.yml + lab.yaml
dsoxlab check <id-du-lab>         # les tests du lab
python3 -m pytest tests/ -q       # les méta-tests du dépôt
python3 scripts/gen_catalog.py    # rafraîchir le catalogue du README
```

Le catalogue est généré à partir des vrais `lab.yaml` : lancez `gen_catalog.py`
après avoir ajouté ou renommé un lab, et `--check` pour vérifier.

## Conventions

- **Id de lab :** `<section>-<slug>`, identique au nom du répertoire.
- **Commits :** en français, sujet factuel qui dit **ce qui a changé et
  pourquoi**, sans préfixe conventionnel. Le corps raconte ce qui a été mesuré,
  y compris les mesures jetées en route : elles valent souvent plus que le
  résultat.
- **i18n :** le fichier sans suffixe est l'anglais (langue officielle du dépôt),
  le `*.fr.md` est la traduction française. Les deux doivent dire la même chose.
- **Style :** pas d'emoji ni de tiret cadratin dans ce que l'apprenant lit. Les
  messages d'assertion enseignent : ils disent ce qui ne va pas et pourquoi, pas
  seulement ce qui était attendu.

## Pull requests

Travaillez sur une branche dédiée, gardez `dsoxlab validate-structure` vert,
écrivez une description claire et reliez la capacité ou l'issue traitée.
