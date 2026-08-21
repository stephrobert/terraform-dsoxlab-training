# Scénario : un examen blanc dont les réponses se prouvent

**Sous-objectif d'examen visé : Terraform Associate 004, 4c (variables et outputs) en
principal, avec 4d, 4f, 4g et 7b mobilisés par les questions de contrôle.**

Un QCM corrigé à la main ne prouve rien et se triche tout seul : ici les réponses voyagent
dans un fichier de variables, Terraform les corrige lui-même, et quatre questions n'ont de
réponse qu'après avoir construit une infrastructure. Piège traité, celui des annales
périmées : les nouveautés du 004 ne sont ni le fichier de verrouillage ni `moved`, ce sont
4f (`depends_on`, `create_before_destroy`), 4g, 4h et 8c.

## Capacité visée

Répondre aux huit objectifs du programme Associate 004 dans un format machine, et prouver
chaque réponse par l'état d'une configuration réellement initialisée, appliquée et
inspectée : savoir répondre, et savoir le montrer par la CLI. Ne rien affirmer sans preuve.

## D'où part l'apprenant

`challenge/work` contient deux répertoires. Dans `examen/` : un `questions.fr.md` de 40
questions `q01` à `q40`, étiquetées par objectif officiel, mélangeant choix unique,
vrai/faux et réponses multiples (notées par lettres triées, par exemple `ac`) ; un
`reponses.auto.tfvars` où chaque entrée vaut `"???"` ; un barème fourni, à ne pas modifier,
qui déclare `variable "reponses"` en `map(string)` et compare l'empreinte `sha256` salée de
chaque réponse à une table d'empreintes, aucune réponse n'existant en clair. Dans
`atelier/` : une configuration trouée par des `???` sur `local`, `null` et `random`, sans
`.terraform/`, sans state, sans fichier de verrouillage.

## L'état à atteindre

1. `atelier` est initialisé, les trois providers contraints en `~>`, le verrou présent.
2. `atelier` est appliqué et porte des objets gérés et exactement un bloc `data`, une
   dépendance déclarée par `depends_on`, une resource remplacée en `create_before_destroy`.
3. Une `precondition`, une `postcondition` et un bloc `check` passent tous, et une variable
   `sensitive` a sa valeur en clair dans le state alors que son output est masqué.
4. Juste après l'apply, `atelier` est stable : aucun changement en attente.
5. `reponses.auto.tfvars` ne contient plus aucun `???` et fournit les 40 réponses, dont
   `q37` à `q40` qui portent sur l'état réel de `atelier` : nombre d'objets en
   `mode: managed`, adresse du bloc en `mode: data`, code de sortie du plan de stabilité,
   présence en clair de la valeur sensible dans le state.
6. Le score global atteint au moins 80 %, aucun objectif n'est en dessous de 50 %, et la
   table d'empreintes du barème est intacte.

## Comment on le prouve

- Dans `examen`, `terraform output -json` expose `corrige` (un booléen par question),
  `score`, `score_par_objectif` et `sans_reponse` : les tests exigent `sans_reponse` vide,
  un nombre d'entrées fausses sous le quota toléré, et `score` au dessus de 80.
- Rien n'est codable en dur, ces sorties étant calculées par le barème depuis
  `var.reponses`. Les tests comparent en plus `output -json empreintes` à la liste qu'ils
  détiennent, ce qui détecte un barème modifié : ils ne stockent que des `sha256`.
- Dans `atelier`, `terraform show -json` sert de source unique : objets comptés par `mode`,
  adresse du bloc `data`, valeur sensible en clair dans le state ; le plan converti en JSON
  confirme `create_before_destroy` et le `depends_on`. `plan -detailed-exitcode` sort en 0
  juste après l'apply, puis en 2 une fois la dérive provoquée hors code par le test.
- Croisement final : les tests recalculent les quatre valeurs de contrôle depuis l'état de
  `atelier` et exigent la concordance avec les réponses fournies. Deviner `q37` à `q40`
  sans construire l'atelier échoue sur l'état, construire sans répondre échoue sur le
  score. Aucun `.tf` de l'apprenant n'est relu. Faute d'argument write-only dans `local`,
  `null` et `random`, 4h reste évalué par le questionnaire seul, et le lab l'annonce.
