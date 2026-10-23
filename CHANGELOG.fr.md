# Journal des modifications

**Language:** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

Tous les changements notables de ce projet sont consignés dans ce fichier. Le
format s'appuie sur [Keep a Changelog](https://keepachangelog.com/).

Ce dépôt est un **catalogue de contenu**, pas une bibliothèque : il n'est pas
versionné et ne publie pas de release. Les entrées ci-dessous datent les
changements du catalogue, et l'unité qui compte est le lab.

## [0.2.2] - 2026-10-23

### Ajouté

- Un verdict ne peut plus être commité avec ce qu'il mesure. Le hook
  `verdicts-et-commun-separes` refuse un commit portant `validation-labs.json`
  à côté de ce que le cycle joue : `challenge/tests/`, `setup.yaml`,
  `cleanup.yaml`, `lab.yaml` d'un lab, et l'outillage partagé. Il est lui-même
  éprouvé, dans les deux sens, par un hook à lui.

  Cela ferme un cas **qu'aucune mesure ne rattrape après coup**. La péremption
  d'un verdict se jugeait en comparant des DATES, et cette comparaison s'est
  trompée dans les deux sens le 2026-10-22 : une correction commitée avec les
  verdicts qu'elle périmait est passée pour saine, et des labs réattestés sur
  une branche sont ressortis « à réattester » après leur fusion en squash,
  contenu inchangé. Quand une pull request squashée retouche un test *après* sa
  campagne, le commit unique porte les deux et le squash a détruit ce qui les
  distinguait. Cela ne se constate pas, donc cela s'empêche.

  L'énoncé reste autorisé à côté d'un relevé : il n'est pas joué par le cycle,
  et l'interdire obligerait à une campagne pour une coquille.

### Corrigé

- `pipelineMustNotLeakSecretsInConfig` est retiré du `.plumber.yaml`, où il
  était déclaré deux fois. Plumber a supprimé ce contrôle et répond « was
  removed and is now ignored: secret detection is no longer part of Plumber;
  remove this block ». Le garder laissait croire que la détection de secrets
  était couverte ici. Elle ne l'est pas, et c'est `detect-private-key` qui s'en
  approche, en hook.

## [0.2.1] - 2026-10-19

### Modifié

- **Chaque `doc_url` pointe désormais `www.stephane-robert.info`.** Le site est
  passé de `blog.` à `www.`, et l'ancien hôte redirige en 301 vers le même
  chemin. Rien n'était cassé : `validate-structure --check-urls` suit les
  redirections, et ce catalogue était vert avant qu'une ligne change. La
  migration est une mise au propre et non une réparation : un `doc_url` doit
  pointer la page, pas dépendre d'une redirection qu'il faudra bien retirer un
  jour.

  Les chemins sont identiques entre les deux hôtes : seul l'hôte a changé. Les
  359 `doc_url` que les catalogues déclarent ont été cherchés dans le dépôt du
  site, hors réseau : ils y existent tous, y compris vingt-trois pages que
  l'ancien hôte rendait en 404.

## [0.2.0] - 2026-10-17

### Modifié

- **Le validateur lit le contrat, plus l'encadré du terminal.**
  `scripts/valider-labs.py` lisait le score dans ce que `dsoxlab check`
  *affiche*. Cet encadré est de l'interface : il a changé en dsoxlab 0.4.0 et
  la regex a cessé de trouver quoi que ce soit. Il lit désormais
  `check --json`, qui porte un `schema`, et cette lecture vit dans
  `scripts/verdict_check.py`, **identique dans les douze catalogues**.

- **Trois verdicts, pas deux.** Une exécution dont tous les tests collectés ont
  skippé n'a rien mesuré : elle est **SKIP**, ni verte ni rouge, et reste à
  mesurer. La peindre en rouge accuserait le lab de ce qui manque au poste.
  `--check` sort donc en `10` dans ce cas, contre `1` pour un ROUGE, à l'image
  de `dsoxlab doctor --strict` où 9 se répare et 10 se remesure.

- **Le README prend la structure de référence** commune aux douze catalogues :
  quatorze sections, dans les deux langues. Sept d'entre elles décrivent
  dsoxlab et non le sujet, et sont donc identiques partout.

### Exige

- **dsoxlab 0.4.1 ou plus récent**, qui a introduit le champ `status` de
  `check --json`. Sans lui, le validateur refuse de conclure plutôt que de
  deviner.

## [0.1.1] - 2026-10-14

### Modifié

- Dix-huit verdicts rejoués avec la dsoxlab 0.3.5.
- La procédure de release réatteste les labs modifiés depuis leur verdict.

### Corrigé

- Cinq actions GitHub remises à jour.

## [0.1.0] - 2026-10-09

### Ajouté

- **La section `hcp-terraform` est complète**, sept labs jouables sans compte
  plus un huitième, optionnel, qui franchit la frontière. Chacun a été éprouvé
  dans les deux sens et dégradé volontairement pour vérifier qu'il discrimine.
  - `hcp-terraform-overview` joue un run en deux temps avec les plans
    enregistrés, ce qui reproduit en local la division plan/apply d'un run
    distant. Trois refus mesurés lui donnent son sens : un plan rejoué est
    périmé, une variable ne se change pas à l'apply, et un plan sans changement
    n'est pas applicable.
  - `hcp-workspaces` établit que `terraform validate` répond « Success » sur
    deux fautes qui font échouer l'`init`.
  - `remote-runs` fait analyser le flux JSON d'un run **qui a échoué en cours de
    route** : le seul résumé que le flux porte est alors celui du plan, qui
    annonce plus que ce qui a eu lieu.
  - `shared-credentials` mesure que `sensitive` protège l'affichage et laisse la
    valeur en clair dans le state.
  - `projects-teams` fait écrire la règle des permissions, qui retient le niveau
    le plus permissif et non le plus spécifique.
  - `premier-run-distant` provisionne HCP Terraform avec le provider `tfe`, puis
    fait exécuter un vrai run distant. C'est le seul lab qui demande un compte ;
    sans jeton, ses tests se skippent au lieu d'échouer.
- **Un guide du jeton HCP Terraform**, `docs/hcp-token.md` et sa traduction :
  créer le jeton, les trois emplacements possibles avec leur priorité mesurée,
  et la confusion avec le jeton OAuth de la GitHub App, qui s'affiche sur la
  même page et donne un `401` impossible à distinguer d'une révocation.
- **`scripts/diagnostic-jeton-hcp.py`**, qui dit lequel des emplacements
  l'emporte, signale les jetons ignorés, contrôle la forme avant d'appeler
  l'API, et n'affiche jamais la valeur d'un jeton.
- **`tests/test_aucun_jeton_versionne.py`**, qui refuse qu'un jeton d'API, une
  clé AWS ou un bloc `credentials` renseigné entre dans le dépôt. Il lit le
  contenu des fichiers, là où un `.gitignore` ne protège que les chemins qu'on a
  pensé à nommer.
- **La gouvernance du dépôt** : `LICENSE` (CC BY 4.0), `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY` et ce journal, en anglais et en français.

### Modifié

- **Le pilotage local est exclu par le dépôt lui-même.** `.claude/` et `todo/`
  n'étaient ignorés que par le `.gitignore` global de la machine de l'auteur :
  sur un autre poste, un `git add -A` les aurait publiés.

## 2026-09-20

### Ajouté

- Les premiers labs de la section `getting-started`, écrits un à un à partir
  d'énoncés qui n'avaient pas de tests.
- Les hooks pre-commit, verts sur tout le dépôt : arrêt net sur les secrets et
  les clés privées, et contrôle que les solutions restent chiffrées.
- Un formulaire d'issue, pour que `dsoxlab support --issue` arrive déjà rempli.

### Corrigé

- `runtime.fixtures`, oublié deux fois : sans cette liste, le répertoire de
  travail reste vide et le lab ne mesure rien.
- Un faux négatif attrapé par le cycle complet, sur `terraform-vs-opentofu`.

## 2026-08-21

### Ajouté

- Premier commit : 87 labs, leurs scénarios et leur ordre dans `meta.yml`.

[Non publié]: https://github.com/stephrobert/terraform-dsoxlab-training/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/stephrobert/terraform-dsoxlab-training/releases/tag/v0.1.1
[0.1.0]: https://github.com/stephrobert/terraform-dsoxlab-training/releases/tag/v0.1.0
