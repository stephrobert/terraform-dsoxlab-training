# Publier une version de terraform-dsoxlab-training

**Langue :** [English](./RELEASING.md) · [Français](./RELEASING.fr.md)

Ce dépôt livre du **contenu de labs**, pas un paquet Python. Une version publie
une **archive `tar.gz`** du catalogue de labs Terraform en assets de release GitHub : pas de PyPI,
pas de wheel, aucun registre d'artefacts externe.

## Ce que contient une version

`release.yml` construit `terraform-dsoxlab-training-<version>.tar.gz` avec :

- `labs/`, `meta.yml`, `meta.fr.yml`, `conftest.py`, `curriculums.yml`
- l'outillage qui rejoue le catalogue : `scripts/`, `tests/`, `docs/`
- `validation-labs.json`, le verdict de la campagne de validation dans
  les deux sens
- les documents de gouvernance (`README`, `LICENSE`, `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY`, `CHANGELOG`), dans les deux langues

Il **exclut** le pilotage local (`.claude/`, `CLAUDE.md`), les fichiers générés
(`.venv/`, caches), le brouillon de l'apprenant (`challenge/work/`), et tout ce
qui porte un secret — le mot de passe du vault et toute clé privée.

Quatre assets sont attachés à chaque release :

| Asset | À quoi il sert |
| --- | --- |
| `terraform-dsoxlab-training-<version>.tar.gz` | le catalogue lui-même |
| `….tar.gz.sha256` | l'intégrité, vérifiable hors ligne |
| `….tar.gz.cosign.bundle` | la signature Cosign keyless |
| `provenance.intoto.jsonl` | la provenance SLSA, l'asset que cherche le contrôle Signed-Releases d'OpenSSF Scorecard |

## Pourquoi trois jobs, et pas un seul

Le workflow est découpé en **construire**, **attester**, **publier**, et ce
découpage est la seule chose qui sépare SLSA Build Level 2 de Level 3.

La documentation GitHub le dit en deux phrases : « Artifact attestations by
itself provides SLSA v1.0 Build Level 2 », et « Reusable workflows can provide
isolation between the build process and the calling workflow, to meet SLSA
v1.0 Build Level 3 ». Tant que le job qui construit l'archive est aussi celui
qui signe sa provenance, rien n'empêche techniquement le build de produire une
provenance qui ment. Le niveau 3 exige que la signature se fasse hors de sa
portée.

D'où `.github/workflows/attester.yml`, appelé comme workflow réutilisable :

- il est le **seul workflow du dépôt** à recevoir `attestations: write` ;
- il reçoit **un nom et une empreinte**, jamais l'archive ni le dépôt : il ne
  fait aucun `checkout` ;
- le job de publication peut écrire la release mais **ne peut pas attester**,
  faute de cette permission ;
- l'archive est recontrôlée contre son empreinte **avant** publication, pour
  qu'un artefact altéré entre deux jobs ne soit pas publié avec une provenance
  qui ne le décrit pas.

## Produire une version

1. Déplacer les entrées `[Non publié]` sous une nouvelle version dans
   `CHANGELOG.fr.md` **et** `CHANGELOG.md`, et ajouter les deux liens.
2. Contrôler le catalogue en local : `dsoxlab validate-structure`,
   `pytest tests/ -q`, et `python3 scripts/valider-labs.py --check` (aucun lab
   ne doit être ROUGE).
3. Ouvrir une pull request pour ce changement, et laisser la CI passer au vert.
4. Une fois fusionnée, taguer le **commit fusionné** et pousser le tag, ce qui
   déclenche `release.yml` :

   ```bash
   git switch main && git pull
   git tag -a vX.Y.Z -m "terraform-dsoxlab-training X.Y.Z"
   git push origin vX.Y.Z
   ```

5. Surveiller l'exécution. Les trois jobs doivent être verts : un job
   `provenance` en échec laisse la release non publiée, plutôt que de la publier
   sans attestation.

## Vérifier une version

Intégrité et contenu :

```bash
sha256sum -c terraform-dsoxlab-training-<version>.tar.gz.sha256
tar tzf terraform-dsoxlab-training-<version>.tar.gz | head
```

Provenance du build. Prouve que l'archive a bien été produite par le workflow de
ce dépôt, et non reconstruite par quelqu'un d'autre :

```bash
gh attestation verify terraform-dsoxlab-training-<version>.tar.gz --repo stephrobert/terraform-dsoxlab-training
```

**La vérification qui atteste le niveau 3** nomme le workflow signataire. Elle
échoue si la provenance a été produite ailleurs que par le workflow
d'attestation isolé, et c'est elle qu'il faut lancer à la première release pour
confirmer que la chaîne tient :

```bash
gh attestation verify terraform-dsoxlab-training-<version>.tar.gz \
  --repo stephrobert/terraform-dsoxlab-training \
  --signer-workflow stephrobert/terraform-dsoxlab-training/.github/workflows/attester.yml
```

Signature Cosign keyless. Les **deux** options de certificat sont obligatoires :
sans elles, `cosign verify-blob` accepte n'importe quelle identité, ce qui vide
la vérification de son sens.

```bash
cosign verify-blob \
  --bundle terraform-dsoxlab-training-<version>.tar.gz.cosign.bundle \
  --certificate-identity-regexp "https://github.com/stephrobert/terraform-dsoxlab-training/.github/workflows/release.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  terraform-dsoxlab-training-<version>.tar.gz
```

> **Piège de version Cosign.** La CI installe **Cosign 3.x**, qui écrit un
> nouveau format de bundle. Un **Cosign 2.x** local répond `no signatures found`
> sur une archive pourtant parfaitement signée : la release n'est pas cassée,
> c'est l'outil local qui ne sait pas lire le format. Vérifiez `cosign version`
> et alignez-le avant de conclure quoi que ce soit.

> Les commits et les tags sont créés par un humain, jamais par un assistant.
