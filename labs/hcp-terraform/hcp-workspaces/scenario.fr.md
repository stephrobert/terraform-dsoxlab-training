# Scénario : deux mots « workspace », deux stratégies de rattachement

**Sous-objectif d'examen visé : 6b.**

L'objectif 6 est évalué en QCM : aucun compte HCP Terraform ici, rien ne part en
exécution distante. Le lab traite les deux pièges qui font tomber les candidats :
confondre le workspace CLI, simple state nommé dans un répertoire, avec le
workspace HCP Terraform, unité d'exécution avec ses variables et ses droits, et
croire que `name` et `tags` cohabitent dans un bloc `cloud`.

## Capacité visée

Écrire un bloc `cloud` correct du premier coup, trancher entre stratégie `name`
et stratégie `tags`, et savoir quel contrôle attrape quelle faute : ce que
`terraform validate` voit, ce que seule l'initialisation du backend voit.

## D'où part l'apprenant

`challenge/work` contient trois répertoires, aucun provider, donc aucun accès
réseau. `nomme/` est à réparer, rattaché par nom au workspace `app-prod`, et
cumule trois fautes : un `backend "local"` cohabite avec le bloc `cloud`, le bloc
`workspaces` déclare à la fois `name` et `tags`, et `organization` pointe sur
`var.organisation`. `etiquete/` est à réparer, rattaché par étiquettes : deux
blocs `cloud` concurrents et un second `workspaces` vide, l'état visé imposant
une map clé-valeur, un `project` et donc un `required_version` compatible avec la
forme map. `questionnaire/` fournit un `questionnaire.tf` à ne pas modifier :
variable `reponses` d'un type objet strict, blocs `validation` qui refusent tout
mot hors de l'énuméré, `output` qui republient les réponses. Seul
`reponses.auto.tfvars` est à remplir, ses valeurs étant remplacées par `???`.

## L'état à atteindre

1. `nomme/` et `etiquete/` sont valides : plus aucun diagnostic d'erreur, ni
   conflit `cloud` contre `backend`, ni `cloud` en double.
2. `nomme/` est rattaché par la stratégie `name` sur le workspace exact
   `app-prod`, et son `organization` est une chaîne littérale.
3. `etiquete/` est rattaché par la stratégie `tags`, avec `project` déclaré et
   sans aucun `name`.
4. Aucun des deux ne s'initialise vraiment : l'initialisation s'arrête au jeton
   absent ou à la découverte du service, frontière assumée du lab.
5. Le questionnaire s'applique et ses outputs tranchent : workspace CLI contre
   workspace HCP Terraform, les quatre modes d'exécution et le réglage par défaut
   d'un workspace, les workspace variables non évaluées en mode Local, les deux
   seules opérations qui ignorent le verrou, le réglage à activer avant tout plan
   de destruction, la règle de suppression, les versions minimales pour `project`
   et pour les tags clé-valeur, et les messages exacts du conflit `cloud` contre
   `backend` et du jeton manquant.

## Comment on le prouve

Les tests n'ouvrent aucun `.tf`. Pour les points 1 à 3 ils lancent
`terraform validate -json` puis `terraform init -input=false -json`, ne gardent
que les objets de type `diagnostic` et raisonnent sur leur `summary` : les résumés
`Conflicting 'cloud' and 'backend' configuration blocks are present`,
`Duplicate HCP Terraform configurations`, `Variables not allowed` et
`Missing workspace mapping strategy` doivent tous avoir disparu.

La stratégie retenue se prouve par sonde : dans `nomme/`, initialiser avec
`TF_WORKSPACE` posé sur un autre nom doit produire `Specified workspace "name"
conflicts with TF_WORKSPACE environment variable.`, et la même commande avec
`TF_WORKSPACE=app-prod` ne doit plus la produire, ce qui identifie le nom exact ;
dans `etiquete/`, aucune valeur ne déclenche ce conflit, puisque `name` est
absent. Le point 4 est un contrôle négatif : le code de retour de
l'initialisation n'est jamais assuré, seule compte l'absence de ces résumés.

Le questionnaire suit les autres labs de la section : `terraform apply
-auto-approve -input=false`, lecture de `terraform output -json`, égalité stricte
sur les listes ordonnées, égalité d'ensembles sinon, puis
`terraform plan -detailed-exitcode` attendu en code 0. Un `challenge/work` vide
ne produit ni output, ni `valid: true`, ni diagnostic de sonde.
