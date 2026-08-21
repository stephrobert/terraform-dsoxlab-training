# Scénario : auditer des credentials HCP Terraform sans compte HCP

**Sous-objectif d'examen visé : 6c.**

L'objectif 6 est évalué en QCM : on ne vous demandera pas de cliquer dans HCP
Terraform, on vous demandera de dire ce qui cloche dans une configuration. Deux
pièges ici : croire qu'une clé statique rangée en variable d'environnement est
« sécurisée », et croire que `tfe_outputs` se lit comme un data source ordinaire.

## Capacité visée

Diagnostiquer un workspace HCP Terraform authentifié par clés statiques, nommer
chaque défaut, et produire la configuration corrigée en dynamic provider
credentials OIDC : variables d'environnement exactes, audience, trust policy
IAM cadrée.

## D'où part l'apprenant

`challenge/work` contient `dossier-audit/`, en lecture seule, trois extraits
d'une plateforme existante :

1. `variables-workspace.json`, l'export des variables du workspace `prod-app` :
   `AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY` en variables d'environnement,
   la seconde avec `"sensitive": false`, aucune variable `TFC_AWS_*`, et l'ARN
   du rôle IAM déjà créé côté AWS.
2. `trust-policy.json` : aucune condition sur le claim `aud`, et un `sub` en
   `StringLike` sur `organization:*:project:*:workspace:*:run_phase:*`.
3. `app.tf` : il lit `data.tfe_outputs.reseau` par l'attribut `values` et
   republie la valeur dans un output racine sans `sensitive = true`.

`main.tf` est fourni et **ne doit pas être modifié** : providers `local` et
`null` uniquement, il consomme les réponses et fabrique les artefacts. Reste à
remplir `reponses.auto.tfvars`, dont toutes les valeurs sont des `???` : liste
des défauts (identifiants donnés en commentaire), map des variables
d'environnement à poser, audience par défaut, attribut de `tfe_outputs` pour
une valeur non sensible, valeurs possibles de `run_phase`, motif `sub` corrigé.

## L'état à atteindre

1. Le state contient la ressource managée `local_file.trust_policy_corrigee`,
   dont le contenu est un JSON valide.
2. Ce JSON porte une condition `StringEquals` sur `app.terraform.io:aud` égale
   à `aws.workload.identity`, absente de la policy d'origine, et un `sub` cadré
   sur l'organisation et le projet réellement présents dans `dossier-audit/`.
3. L'output `variables_dynamiques` vaut exactement `TFC_AWS_PROVIDER_AUTH` à
   `"true"` et `TFC_AWS_RUN_ROLE_ARN` à l'ARN lu dans l'export, et l'output
   `cles_statiques_restantes` est vide : plus aucune trace des deux clés AWS.
4. L'output `attribut_tfe_outputs` vaut `nonsensitive_values` : `values` est
   marqué sensible en entier et ne peut alimenter un output racine ordinaire.
5. L'output `defauts_identifies` contient les cinq identifiants attendus, ni
   plus ni moins, et la configuration est idempotente.

## Comment on le prouve

Les tests n'ouvrent jamais un `.tf` de l'apprenant. `terraform show -json`
fournit `values.root_module.resources` : on y cherche une entrée
`mode: managed` de type `local_file` nommée `trust_policy_corrigee`, on parse
son attribut `content` comme du JSON et on vérifie les conditions `aud` et
`sub` clé par clé. `terraform output -json` fournit le reste : ensembles triés
pour `defauts_identifies` et `phases_run`, égalité stricte sur la map
`variables_dynamiques`, liste vide pour `cles_statiques_restantes`, chaînes
exactes pour `attribut_tfe_outputs` et `audience_par_defaut`. Enfin
`terraform plan -detailed-exitcode` doit rendre 0.
