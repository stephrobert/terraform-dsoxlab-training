# Scénario : le bloc cloud, prouvé sans compte HCP

**Sous-objectif d'examen visé : 6a.**

L'objectif 6 est évalué **en QCM uniquement** : aucune manipulation sur la plateforme n'est demandée
le jour de l'examen. Ce lab ne crée donc **aucun compte HCP Terraform** et n'exécute **aucun run
distant** ; il valide la seule chose qui se joue sur votre poste, la configuration du bloc `cloud`.

## Capacité visée

Écrire un bloc `cloud` valide, diagnostiquer les quatre erreurs que Terraform refuse hors ligne
(coexistence avec un `backend`, `name` et `tags` ensemble, interpolation, `organization` absente),
et migrer un `backend "remote"` hérité vers un bloc `cloud`.

## D'où part l'apprenant

`challenge/work/` contient quatre répertoires Terraform indépendants, sans aucun provider :

1. `cli-driven/main.tf` : bloc `cloud` dont `organization`, `workspaces.project` et
   `workspaces.name` valent `???`, et qui traîne encore un bloc `backend "local"` hérité.
2. `selection-par-tags/main.tf` : bloc `cloud` déclarant **à la fois** `name` et `tags`, avec une
   `organization` interpolée depuis `var.org`.
3. `heritage/main.tf` : `backend "remote"` de l'époque Terraform Cloud, avec un argument `project`
   que ce backend n'accepte pas.
4. `automation/cloud.tf.json` : le même réglage qu'en 1, mais en **syntaxe JSON native** (la forme
   des configurations générées), valeurs à `???` elles aussi.

`CONSIGNES.fr.md` fixe les valeurs imposées : organisation `stephrobert-terraform-labs`, project
`professional`, workspace `professional-01-cloud-block`, tag `couche = "reseau"`.

## L'état à atteindre

1. `cli-driven/` ne garde qu'un seul emplacement de state, le bloc `cloud`, porteur des trois
   valeurs imposées : `Conflicting 'cloud' and 'backend' configuration blocks are present` a disparu.
2. `selection-par-tags/` retient la stratégie `tags` seule, sans `name`, avec une `organization` en
   valeur littérale : le bloc `cloud` n'admet aucune référence à une variable.
3. `heritage/` est passé de `backend "remote"` à `cloud` et conserve son `project`, que l'ancien
   backend rejetait.
4. `automation/cloud.tf.json` reste un JSON bien formé, porte les mêmes valeurs que `cli-driven`, et
   Terraform le charge comme une configuration à part entière.
5. Partout, le **seul** diagnostic restant est `Required token could not be found` : le local passe.

## Comment on le prouve

Les tests neutralisent toute identité (`TF_CLI_CONFIG_FILE` vers un fichier vide, variables
`TF_TOKEN_*` et `TF_CLOUD_*` retirées), puis, dans chaque répertoire :

- `terraform init -json -input=false`, dont la sortie JSONL est lue ligne par ligne pour collecter
  `diagnostic.summary` et `message_code`. Aucune sortie humaine n'est parsée.
- Assertion centrale : l'ensemble des `diagnostic.summary` vaut exactement
  `{"Required token could not be found"}`. Un conflit `name`/`tags`, une interpolation ou une
  `organization` manquante ajouterait un summary supplémentaire.
- Migration : `heritage/` doit émettre le `message_code` `initializing_terraform_cloud_message` et
  non plus `initializing_backend_message`.
- `terraform init -backend=false` puis `terraform validate -json` : `valid` vaut `true` et
  `error_count` vaut `0`, sans jamais contacter la plateforme.
- `automation/cloud.tf.json` relu par `json.load` : comparaison de `terraform.cloud.organization`,
  `.workspaces.project` et `.workspaces.name` aux valeurs imposées.
- Garde-fou : un répertoire vide n'émet ni `initializing_terraform_cloud_message` ni diagnostic de
  token, donc il échoue sur la première assertion.
