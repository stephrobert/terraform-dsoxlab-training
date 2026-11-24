# Le cycle de vie d'une ressource se lit dans le plan

## La situation

**Sous-objectif d'examen visé : 1c.**

Déclarer un bloc `resource {}` est trivial ; dire avant d'appliquer si Terraform
va mettre à jour en place ou détruire puis recréer ne l'est pas. Piège traité :
`depends_on` partout, alors que la doc officielle le classe en dernier recours.

## Capacité visée

Construire une configuration de quatre ressources dont l'ordre de création
découle uniquement des références, obtenir un remplacement avec création avant
destruction, et prouver dans le plan JSON la différence entre `update`,
`create` puis `delete`, et l'inverse.

## D'où part l'apprenant

`challenge/work` contient quatre fichiers, aucun state, aucun `.terraform` :

- `versions.tf` et `variables.tf` : complets, à ne pas toucher. Providers
  `local` et `random` épinglés, `required_version >= 1.15.0`, variables
  `etiquette` (string, défaut `"v1"`) et `generation` (number, défaut `1`).
- `main.tf` : quatre blocs `resource {}` amorcés, `???` sur les labels, sur les
  références entre ressources, sur le bloc `lifecycle`, sur le meta-argument de
  dépendance. `outputs.tf` : deux `output` dont les valeurs sont des `???`.
  Ces `???` sont des erreurs de syntaxe : rien ne s'applique en l'état.

## L'état à atteindre

1. Le state contient exactement quatre ressources en `mode: managed`, aux adresses
   `random_pet.hote`, `local_file.fiche`, `terraform_data.sceau`, `local_file.journal`.
2. `local_file.fiche` tire son contenu de `random_pet.hote.id` : dépendance
   implicite, sans `depends_on`, et porte `create_before_destroy = true`.
3. `terraform_data.sceau` porte `input = var.etiquette` et
   `triggers_replace = random_pet.hote.id` ; `random_pet.hote` a des `keepers`
   liés à `generation`.
4. `local_file.journal` dépend de `terraform_data.sceau` par le seul `depends_on`,
   sans référencer aucun attribut : dépendance comportementale, le seul cas justifié.
5. Les outputs exposent le chemin de la fiche et `terraform_data.sceau.output`,
   et un `apply` suivi d'un `plan` ne propose plus aucun changement.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les fichiers `.tf`. Aucun
contrôle ne passe sur un répertoire vide, ni sans câbler les références.

- `terraform show -json` : `values.root_module.resources` contient les quatre
  adresses, toutes en `mode: managed` ; dans `configuration.root_module.resources`,
  `depends_on` est présent sur `local_file.journal`, absent sur `local_file.fiche`.
- `terraform output -json` : les deux sorties existent, la valeur du sceau vaut
  l'étiquette appliquée. `terraform plan -detailed-exitcode` sort en 0 juste
  après l'apply, ce qui prouve l'idempotence.
- `terraform plan -var 'etiquette=v2' -json` : l'action planifiée pour
  `terraform_data.sceau` vaut `["update"]`, la mise à jour en place.
- `terraform plan -var 'generation=2' -json` : `random_pet.hote` est remplacé,
  `terraform_data.sceau` aussi par propagation du trigger, et `local_file.fiche`
  affiche `["create", "delete"]` dans cet ordre, signature de
  `create_before_destroy`, là où l'absence de la règle donnerait `["delete", "create"]`.

Référence : https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/declarer-ressources/

## 🎯 Challenge : quatre ressources, quatre opérations

### Point de départ

`challenge/work` contient quatre blocs `resource {}` et deux `output`, tous
troués par des `???`. `versions.tf` et `variables.tf` sont **complets, à ne pas
modifier** : ils déclarent les variables `etiquette` (string) et `generation`
(number).

Les `???` sont des erreurs de syntaxe : `terraform init` échoue en l'état.
Chaque trou porte au-dessus de lui un commentaire qui énonce l'attendu.

### ✅ Objectif

Câbler la configuration pour que le state contienne exactement quatre ressources
gérées, aux adresses `random_pet.hote`, `local_file.fiche`,
`terraform_data.sceau`, `local_file.journal` :

1. **`random_pet.hote`** porte des `keepers` liés à `var.generation` : un
   changement de génération doit le remplacer.

2. **`local_file.fiche`** tire l'id de l'hôte dans son `filename` (dépendance
   **implicite**, sans `depends_on`), et porte `create_before_destroy = true`.

3. **`terraform_data.sceau`** porte `input = var.etiquette` (mise à jour en place
   quand l'étiquette change) et `triggers_replace` valant l'id de l'hôte
   (remplacement quand il change).

4. **`local_file.journal`** dépend du sceau par le **seul** `depends_on`, sans
   référencer aucune de ses données : c'est une dépendance de comportement.

5. Les outputs exposent le chemin de la fiche et l'attribut `output` du sceau.

Après votre `apply`, `terraform plan` ne doit plus rien proposer.

### 🧭 Ce que les tests lisent

Le tableau `resource_changes[].actions` du plan JSON. Les tests vérifient les
signatures des quatre opérations :

- `etiquette=v2` : le sceau doit être en **`["update"]`** (mise à jour en place).
- `generation=2` : la fiche doit être en **`["create", "delete"]`**
  (`create_before_destroy`), pas `["delete", "create"]`.

Des blocs mal câblés ne produisent pas ces signatures.

### 🔍 Validation

```bash
dsoxlab check write-code-declare-resources
```

Sept tests. Ils décodent `terraform show -json` (state et configuration),
`output -json` et le plan JSON. Aucun ne lit vos `.tf`.
