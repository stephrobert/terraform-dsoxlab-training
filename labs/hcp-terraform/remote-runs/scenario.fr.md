# Scénario : le flux qu'un run renvoie, et les trois façons de le lancer

**Sous-objectif d'examen visé : 6a, analyser le workflow d'un run HCP Terraform.**

L'objectif 6 est évalué en QCM, et ne demande aucun compte. Mais ce qu'une CLI reçoit d'un
run distant, « Running plan in HCP Terraform. Output will stream here », est exactement le
flux structuré que `terraform apply -json` produit en local. Ce lab en enregistre donc un
vrai, et le lit.

Un run est passé cette nuit. Deux ressources existent, une troisième non, et le résumé que
porte le flux annonce trois ajouts. Quelqu'un doit établir ce qui s'est réellement passé.

## Capacité visée

Lire le flux d'un run plutôt que son dernier message : distinguer ce qui a été annoncé de
ce qui a eu lieu, retrouver les ressources en échec, et savoir lequel des trois workflows
autorise quoi.

## D'où part l'apprenant

`challenge/work` contient trois répertoires :

1. `flux/`, une configuration fournie à trois ressources `local_file`. La troisième
   **échoue volontairement** : elle écrit sous un chemin dont le parent est un fichier.
   L'apply se termine donc sur un code non nul, et c'est le résultat attendu.
2. `analyse/`, une configuration trouée de cinq `???`, qui doit lire le flux enregistré et
   en tirer ses conclusions.
3. `questionnaire/`, cinq réponses à poser dans `reponses.auto.tfvars`, sur les trois
   workflows.

## L'état à atteindre

1. Le run est joué dans `flux/` en enregistrant son flux :
   `terraform apply -auto-approve -json > run.jsonl`. Deux fichiers sont créés, le
   troisième non.
2. `par_type` compte les messages du flux par type, lus dans le flux et non écrits à la
   main.
3. `resume_annonce` donne l'objet `changes` du seul `change_summary` que le flux porte.
4. `adresses_abouties` et `adresses_en_echec` séparent les ressources qui ont abouti de
   celle qui a échoué.
5. `ecart_entre_annonce_et_abouti` donne la différence entre les deux, et c'est tout
   l'intérêt de l'exercice.
6. Les cinq réponses établissent quel workflow interdit un remote apply, ce qu'un run CLI
   envoie, d'où viennent ses valeurs de variables, quel workflow est recommandé en
   non-interactif, et quel fichier exclut du contenu de l'envoi.

## Pourquoi le run échoue, et pourquoi c'est le sujet

Mesuré le 2026-09-25 sur Terraform 1.16.1, sur la même configuration selon qu'elle aboutit
ou non :

| Run | Messages `change_summary` |
| --- | --- |
| qui aboutit | deux, `plan` puis `apply` |
| qui échoue en cours | **un**, celui du `plan` seul |

Sur un run interrompu, le seul résumé que le flux porte est celui que le plan **annonçait**.
Il dit `add: 3` là où deux ressources ont été posées, et rien dans ce message ne le
signale. Ce qui a eu lieu ne se lit que dans les messages `apply_complete`.

Un run qui réussit ne permettrait pas de le mesurer : tout ce qui est planifié aboutit, et
les deux moitiés du flux racontent la même chose.

## Comment on le prouve

Les tests relisent `flux/run.jsonl` et recalculent ce que l'analyse aurait dû rendre : ce
qui est comparé, c'est l'analyse de l'apprenant à la vérité de son propre flux, jamais à un
chiffre gelé. Un flux écrit à la main ne passerait pas davantage : les tests exigent que
l'état du système concorde, deux fichiers présents, l'impossible absent, et exactement deux
ressources dans le state.

Vérifié en dégradant la solution : filtrer sur `operation == "apply"`, qui est le réflexe
juste sur un run qui aboutit, fait tomber le score à 8/12 ; lire les adresses dans
`planned_change` au lieu d'`apply_complete` le fait tomber à 10/12.
