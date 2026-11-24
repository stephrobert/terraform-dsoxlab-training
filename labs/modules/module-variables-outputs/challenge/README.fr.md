# L'interface d'un module est un contrat

## La situation

**Sous-objectif d'examen visé : 2e (variables et outputs, types complexes), en appui sur 4a (créer un module) et 2f (données sensibles).**

Un module se juge à ce qu'il accepte en entrée et à ce qu'il garantit en sortie. Ce lab traite quatre pièges que le tandem `type` plus `default` ne suffit pas à couvrir : un attribut d'objet facultatif, un `null` passé explicitement, une sortie qui doit refuser de se publier, et un secret ré-exporté qui fait échouer le plan tant qu'il n'est pas marqué.

## Capacité visée

Concevoir l'interface d'un module réutilisable : rendre facultatif un attribut d'objet avec `optional()` plutôt que multiplier les variables, blinder une variable contre un `null` explicite, rejeter une valeur hors bornes avec un message exploitable, garder une sortie sous `precondition`, et ré-exporter correctement une valeur sensible venue du module enfant.

## D'où part l'apprenant

`challenge/work/` contient un projet Terraform incomplet. Aucune VM, aucun compte distant : seuls `hashicorp/local` et `hashicorp/random` sont utilisés, `terraform init` est déjà passé et `.terraform.lock.hcl` est en place. Le lab tourne partout où `terraform` 1.15 ou plus est sur le PATH, sans réseau. Sont déjà corrects et ne doivent pas être retouchés : `versions.tf` (`required_version = ">= 1.15.0"`), le `main.tf` du module enfant `modules/artefact/` (il crée `random_password.this` de longueur `var.longueur_secret` et `local_file.this` dont le nom dérive de `var.depot`), et le `main.tf` racine, qui appelle le module deux fois : `module "complet"` fournit tous les attributs, `module "minimal"` ne fournit que `depot = { nom = "livraison" }`.

Trois fichiers sont troués. `modules/artefact/variables.tf` :

```hcl
variable "depot" {           # object : nom (string, requis),
  ???                        # retention_jours (number, défaut 7),
}                            # chiffre (bool, défaut true)
variable "etiquette" {       # string, défaut "artefact"
  ???                        # un null explicite doit donner le défaut
}
variable "longueur_secret" { # number, défaut 16, refusé hors de 12..64
  ???
}
```

`modules/artefact/outputs.tf` :

```hcl
output "resume" {  ???  }    # object typé : nom, retention_jours, chiffre, etiquette
output "secret" {  ???  }    # dérivé de random_password.this.result
output "chemin" {  ???  }    # local_file.this.filename, publié seulement si chiffre
```

`outputs.tf` racine expose `resume_minimal` (le `resume` de `module.minimal`) et `secret_partage` (le `secret` de `module.complet`), tous deux troués. En l'état, les `???` ne sont pas du HCL valide et rien ne plane.

## L'état à atteindre

1. Le travail est bien dans un module appelé deux fois, pas dupliqué à la racine.
2. L'appel minimal aboutit sans fournir `retention_jours` ni `chiffre` : le contrat du module comble les manques par 7 et `true`.
3. Un appel qui passe `etiquette = null` obtient quand même `"artefact"` : la variable refuse le null au lieu de le propager.
4. `longueur_secret = 8` est rejeté avant toute création, avec un message qui nomme les bornes.
5. Le secret produit par le module fait exactement la longueur demandée et remonte à la racine sans être lisible dans les sorties courantes.
6. La sortie `chemin` refuse de se publier quand le dépôt n'est pas chiffré, et le plan s'arrête là.
7. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne parsent aucune sortie humaine. Ils lancent Terraform dans `challenge/work` et ne lisent que du JSON ou des codes retour. Les variantes fautives sont produites dans des copies temporaires du projet, jamais dans `work`.

1. `terraform show -json` : `values.root_module.child_modules` compte deux entrées, et `configuration.root_module.module_calls` porte bien `complet` et `minimal`. Une configuration à plat échoue ici.
2. `terraform output -json` : `resume_minimal` vaut exactement `{"nom": "livraison", "retention_jours": 7, "chiffre": true, "etiquette": "artefact"}`, alors que l'appel ne fournit que `nom`. Seul `optional(type, defaut)` produit ce résultat : sans lui, le plan échouerait sur un objet incomplet, et avec un `optional()` sans second argument les deux champs sortiraient à `null`.
3. Copie du projet où l'appel minimal reçoit `etiquette = null` : après apply, `resume_minimal.etiquette` vaut toujours `"artefact"`. Sans `nullable = false`, ce JSON contient `null`, comportement vérifié en 1.15.4.
4. Copie du projet où `module "complet"` reçoit `longueur_secret = 8` : `terraform validate -json` renvoie `"valid": false` et un diagnostic de sévérité `error` dont le `summary` est `Invalid value for variable`. Le code retour est non nul.
5. `terraform output -json` : `secret_partage` porte `"sensitive": true` et sa valeur fait la longueur attendue. Un test de contrôle retire ce marquage dans une copie et vérifie que `terraform plan` y sort en code non nul : la sensibilité remonte du module enfant, et un output racine non marqué est refusé.
6. Copie du projet où `module "complet"` reçoit `chiffre = false` : `terraform plan -json` produit un diagnostic `error` signalant l'échec d'une precondition sur une sortie de module, et le code retour est non nul. Sans `precondition`, ce plan réussirait.
7. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply. Un code 2 fait échouer le lab.

## 🎯 Challenge : écrire l'interface d'un module appelé deux fois

### 📦 Le point de départ

`challenge/work` contient un module, `modules/artefact/`, appelé **deux fois**
depuis la racine. Le corps du module fonctionne ; c'est son **interface** qui est
à écrire.

| Fichier | État |
| --- | --- |
| `versions.tf`, `main.tf` | complets, **à ne pas toucher** |
| `modules/artefact/main.tf` | complet, **à ne pas toucher** |
| `modules/artefact/variables.tf` | trois variables, **à écrire** |
| `modules/artefact/outputs.tf` | trois sorties, **à écrire** |
| `outputs.tf` | deux sorties de la racine, **à écrire** |

Les deux appels de `main.tf` sont vos **cahiers des charges** :

```hcl
module "complet" {
  depot           = { nom = "archives", retention_jours = 30, chiffre = true }
  etiquette       = "production"
  longueur_secret = 24
}

module "minimal" {
  depot = { nom = "livraison" }
}
```

C'est l'appel **minimal** qui met l'interface à l'épreuve : il ne fournit qu'un
attribut sur trois, et aucune des deux autres variables.

### ✅ Objectif

Écrire une interface qui **absorbe** cette différence, **refuse** les valeurs
inacceptables, et **protège** ce qui doit l'être.

### 📋 Ce qu'il faut obtenir

1. L'appel minimal aboutit : `retention_jours` vaut **7** et `chiffre` vaut
   **true** sans que l'appelant les fournisse.
2. Un appel qui passerait `etiquette = null` obtient quand même `"artefact"` : la
   variable **refuse le null** au lieu de le propager.
3. `longueur_secret = 8` est **rejeté**, avec un message qui nomme les bornes
   `12` et `64`.
4. La sortie `resume` expose `nom`, `retention_jours`, `chiffre` et `etiquette`,
   défauts comblés compris.
5. Le secret produit remonte jusqu'à la racine **sans être lisible** dans les
   sorties courantes, et fait la longueur demandée par l'appel complet.
6. La sortie `chemin` **refuse de se publier** quand le dépôt n'est pas chiffré :
   le plan s'arrête.
7. `terraform plan -detailed-exitcode` sort en **0** après l'apply.

### ⚠️ Le cœur du sujet

`type` et `default` ne suffisent pas. Quatre mécanismes complètent l'interface :

| Besoin | Mécanisme |
| --- | --- |
| Un **attribut d'objet** facultatif | `optional(type, defaut)` |
| Un **`null` explicite** qui doit rendre le défaut | `nullable = false` |
| Une **valeur hors bornes** refusée | bloc `validation` |
| Une sortie qui **refuse de se publier** | bloc `precondition` |

Et un cinquième, qui ne se devine qu'en butant dessus : une valeur dérivée d'un
`random_password` **contamine** ce qu'elle traverse. Une sortie racine qui la
republie sans le déclarer fait **échouer le plan**.

### 🔍 Validation

`dsoxlab check modules-module-variables-outputs` prouve, par exécution :

- le state porte bien `module.complet` et `module.minimal` : une configuration à
  plat échoue ;
- `resume_minimal` vaut exactement
  `{"nom": "livraison", "retention_jours": 7, "chiffre": true, "etiquette": "artefact"}` ;
- dans une **copie** du projet où l'appel minimal reçoit `etiquette = null`,
  l'étiquette reste `"artefact"` ;
- dans une copie où `longueur_secret = 8`, `terraform validate -json` rend
  `valid: false` avec `Invalid value for variable` ;
- `secret_partage` est marqué sensible et fait 24 caractères ; retirer ce
  marquage dans une copie fait échouer le plan ;
- dans une copie où `chiffre = false`, le plan échoue sur une **precondition** de
  sortie ;
- `plan -detailed-exitcode` rend **0**.

Les variantes fautives sont produites dans des **copies temporaires** : votre
travail n'est jamais modifié.

Bloqué ? `dsoxlab hint modules-module-variables-outputs`.
