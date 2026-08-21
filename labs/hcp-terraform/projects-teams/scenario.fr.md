# Scénario : une attribution d'accès trop large, à ramener au moindre privilège

**Sous-objectif d'examen visé : 6b (gestion des accès dans HCP Terraform).**

L'objectif 6 se passe en QCM et ce lab n'ouvre aucun compte HCP. Le piège tient
en une phrase lue à l'envers : les permissions sont additives, le plus haut gagne.

## Capacité visée

Auditer une attribution d'accès livrée telle quelle, calculer la permission
effective d'une équipe qui cumule plusieurs portées (organisation, project,
workspace), et ramener chaque droit au bon niveau figé (`read`, `plan`, `write`,
`admin` côté workspace, `read`, `write`, `maintain`, `admin` côté project) ou à
un rôle personnalisé quand aucun niveau figé ne descend assez bas.

## D'où part l'apprenant

`challenge/work` est initialisé, `local` et `null` verrouillés, et contient :

- `attributions.auto.tfvars.json` : l'attribution livrée, cinq équipes avec
  leurs clés `organisation`, `projets`, `workspaces` et `type_de_jeton`.
- `besoins.json` : la fiche de besoin par équipe, en lecture seule, lue par un
  `data "local_file"`. Elle dit ce que l'équipe fait, jamais quel rôle lui donner.
- `main.tf` : les `locals` du calcul, troués en `???` sur la table de rang et
  sur la règle de combinaison entre portées. Un `local_file` écrit le rapport.
- `outputs.tf` : `permissions_effectives`, `ecarts_moindre_privilege`,
  `attributions_finales` et `jetons`, déjà écrits, à ne pas modifier.

## L'état à atteindre

1. `audit-conformite`, qui ne fait que lire, perd la permission d'organisation
   `manage-all-workspaces` et garde le seul rôle project `read`.
2. `ci-livraison`, dont les changements sont soumis à approbation, passe du rôle
   workspace `write` à `plan`, et son `type_de_jeton` de `organization` à
   `team` : un jeton d'organisation ne démarre aucun run.
3. `dev-frontend`, qui crée et supprime ses propres workspaces, passe du rôle
   project `admin` à `maintain` : plus de suppression du project, plus de
   déplacement de workspaces, plus de distribution de droits.
4. `observabilite`, qui ne lit que des sorties via `terraform_remote_state`,
   troque le rôle figé `read` contre un rôle personnalisé dont l'accès au state
   vaut `read-outputs-only`.
5. `permissions_effectives` ne contient plus aucun `admin` hors
   `plateforme-admins`, le calcul retenant le niveau le plus élevé reçu.
6. `ecarts_moindre_privilege` est vide : chaque droit vaut ce qu'exige
   `besoins.json`, ni au-dessus ni en dessous.
7. `rapport-acces.json` est régénéré et rien n'est en attente d'application.

## Comment on le prouve

Les tests n'ouvrent ni les `.tf` ni le fichier de variables. `terraform output
-json` porte l'essentiel : `attributions_finales` pour les points 1 à 4,
`permissions_effectives` pour le 5, `ecarts_moindre_privilege` pour le 6.
`terraform show -json` garde la structure, `local_file.rapport` en
`mode: managed` et `data.local_file.besoins` en `mode: data`. Le 7 est un
`terraform plan -detailed-exitcode` attendu en code 0.

Un dernier test défait la triche par valeurs en dur : il copie le répertoire,
remplace l'attribution par un témoin où une sixième équipe reçoit
`manage-all-projects` en plus d'un `read` de workspace, applique, et attend la
permission effective `admin` et l'écart signalé.
