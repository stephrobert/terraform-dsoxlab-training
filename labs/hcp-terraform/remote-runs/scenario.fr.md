# Scénario : le cycle de vie d'un run HCP Terraform

**Sous-objectif d'examen visé : 6a.**

L'objectif 6 est évalué en QCM : aucun compte HCP Terraform, aucune exécution
distante. Le lab traite le piège des questions d'examen sur les runs, où l'ordre
des étapes, ce qu'un speculative plan traverse vraiment et l'incompatibilité
entre apply CLI et workspace relié au VCS se jouent sur des affirmations très
proches les unes des autres.

## Capacité visée

Ordonner sans hésitation les étapes d'un run HCP Terraform, séparer les étapes
obligatoires des étapes conditionnelles, et trancher les affirmations courantes
sur les speculative plans, la file d'attente d'un workspace et les saved plans.
Le tout exprimé dans une structure typée que Terraform valide, puis restitue en
JSON.

## D'où part l'apprenant

`challenge/work` contient trois fichiers. `versions.tf` fixe la contrainte
`required_version` et ne déclare aucun provider : le lab tourne sans réseau et
sans compte. `questionnaire.tf` est fourni et ne doit pas être modifié : il
déclare une variable `reponses` d'un type objet strict, assortie de blocs
`validation` qui refusent toute valeur hors de l'énuméré autorisé, puis les
`output` qui republient les réponses normalisées (`ordre_du_run`,
`etapes_optionnelles`, `declencheurs_speculatifs`, `contournement_file_attente`,
`etat_terminal_sans_changement`, `version_min_saved_plan`, `affirmations`).
Aucune bonne réponse n'y figure : il n'expose que la forme attendue.
`reponses.auto.tfvars` est le seul fichier à remplir : chaque valeur y est
remplacée par `???`, ce qui fait échouer le parsing HCL dès le premier
`terraform plan`. L'énoncé du challenge liste les onze questions et le
vocabulaire exact accepté, repris de la documentation officielle.

## L'état à atteindre

1. `terraform init` puis `terraform apply` aboutissent : le fichier de variables
   satisfait tous les blocs `validation`.
2. `ordre_du_run` liste les onze étapes dans l'ordre officiel, de `pending` à
   `completion`, `cost_estimation` étant intercalée entre le plan et le policy
   check ; `etapes_optionnelles` retient exactement les étapes conditionnelles,
   dont les quatre phases de run tasks, l'estimation de coût et le policy check.
3. `declencheurs_speculatifs` retient les trois déclencheurs réels et écarte les
   intrus ; `contournement_file_attente` distingue le plan-only run de la seule
   phase de planification d'un saved plan, dont l'apply repasse par la file.
4. `etat_terminal_sans_changement` porte l'état exact d'un plan sans changement,
   sans estimation de coût ni policy check, et `version_min_saved_plan` la
   version minimale de Terraform CLI.
5. `affirmations` tranche chaque proposition : un apply CLI est refusé sur un
   workspace relié au VCS, un speculative plan traverse le policy check mais
   jamais l'apply, un apply interrompu laisse dans le state les objets déjà
   modifiés, un run manuel lancé depuis l'interface ne récupère pas le dernier
   commit, et le refresh-only ne corrige pas le drift.

## Comment on le prouve

Les tests lancent `terraform init -input=false` puis
`terraform apply -auto-approve -input=false` dans `challenge/work` et lisent
uniquement `terraform output -json` : égalité stricte de liste ordonnée pour
`ordre_du_run`, égalité d'ensembles pour les listes non ordonnées, égalité de
chaîne pour l'état terminal et la version, comparaison booléenne clé par clé
pour `affirmations`. Un dernier test rejoue `terraform plan -detailed-exitcode`
et exige le code 0. Aucun test ne lit `reponses.auto.tfvars` ni un fichier
`.tf` : un `challenge/work` vide ou laissé avec ses `???` ne produit aucun
output et échoue dès la première assertion.
