# Scénario : Policy as code, qui bloque un run et qui peut passer outre

**Sous-objectif d'examen visé : 6d.**

L'objectif 6 est évalué en QCM : ni compte HCP Terraform, ni run distant. Le
piège traité ici fait tomber les candidats : croire qu'un `hard-mandatory` est
indépassable, alors que c'est le réglage d'override du **policy set** qui
tranche, et non le seul niveau d'enforcement.

## Capacité visée

Déterminer, pour un run donné, si une policy en échec laisse le run continuer,
le bloque avec une porte de sortie, ou le bloque sans recours, selon le
framework (Sentinel, OPA, Terraform policy), le réglage d'override du policy set
et la permission **Manage Policy Overrides**. Et écrire une règle de conformité
qui refuse effectivement un plan non conforme.

## D'où part l'apprenant

`challenge/work` contient une configuration sans aucun provider, rien à créer :

1. `situations.auto.tfvars.json`, non modifiable, typé dans `variables.tf` :
   sept cas de runs décrits par framework, niveau d'enforcement, échec de la
   policy, override autorisé ou non par le policy set, et détention ou non de
   **Manage Policy Overrides**.
2. `verdicts.tf` (un verdict par cas) et `connaissances.tf` (niveaux par
   framework, framework seul admis en policy checks et sa version maximale,
   position des policies vis à vis du cost estimation, édition Free), troués
   de `???`.
3. `plans/plan-conforme.json` et `plans/plan-non-conforme.json`, deux vraies
   sorties de `terraform show -json` capturées avec le provider `local` (la
   seconde crée un fichier en `0777`), et `evaluation.tf`, la règle de
   conformité trouée de `???` qui doit les lire via `jsondecode(file(...))`.

## L'état à atteindre

1. L'output `verdicts` associe à chaque cas une valeur parmi `poursuit`,
   `bloque_surchargeable` et `bloque`.
2. Le cas `advisory` en échec vaut `poursuit` : un advisory n'interrompt jamais
   un run.
3. Le cas `hard-mandatory` dont le policy set autorise l'override, avec un
   utilisateur détenant la permission, vaut `bloque_surchargeable`, pas `bloque`.
4. Le cas `soft-mandatory` avec un utilisateur sans permission vaut `bloque` :
   le niveau seul ne suffit pas, il faut aussi le droit.
5. `niveaux_par_framework` donne trois niveaux pour Sentinel (`advisory`,
   `soft-mandatory`, `hard-mandatory`), deux pour OPA (`advisory`, `mandatory`),
   trois pour Terraform policy (`advisory`, `mandatory overridable`, `mandatory`).
6. `policy_checks` indique que seul Sentinel s'y exécute et qu'ils plafonnent à
   Sentinel `0.40.x` ; `free_tier` donne un policy set, cinq policies, sans VCS.
7. `violations` est vide pour le plan conforme et contient l'adresse de la
   ressource fautive pour le plan non conforme.

## Comment on le prouve

Les tests lancent `terraform init` puis `terraform apply -auto-approve` et lisent
`terraform output -json` : aucun `.tf` n'est relu. Chaque cas est asséré
séparément, et les sept sont bâtis pour qu'aucune réponse constante ne passe
(`bloque` partout échoue sur le cas advisory, `bloque_surchargeable` partout
échoue sur les deux cas sans permission). L'évaluation est contrôlée dans les
deux sens, violations vides pour le plan conforme et adresse attendue pour le
plan non conforme, car une règle qui ne détecte rien passerait un test à sens
unique. Enfin `terraform plan -detailed-exitcode` rend 0 après l'apply, et sur
un `challenge/work` vide il n'existe aucun output : tout échoue.
