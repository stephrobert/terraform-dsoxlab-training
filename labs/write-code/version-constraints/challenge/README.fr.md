# Contraintes de version et lock file

## La situation

**Sous-objectif d'examen visé : 3a (contraintes de version, fichier de verrouillage).**

Une contrainte de version se lit vite et se comprend mal : `~>` borne une série, `=` épingle une version unique, et le bloc `terraform` n'accepte aucune variable. L'apprenant doit poser les bonnes contraintes et le prouver par la sélection réelle et le lock file, sans rouvrir un `.tf`.

## Capacité visée

Contraindre la version de Terraform par un littéral, épingler un provider à une version exacte, en borner un autre avec l'opérateur pessimiste, et savoir que le lock file fige les providers avec des empreintes `h1:` et se committe. Savoir lire la sélection avec `terraform version -json`.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet. Aucune VM, aucun compte distant : `local` et `random` sont utilisés. Le lab tourne partout où `terraform` est sur le PATH, avec accès au registre pour l'init.

Le répertoire contient `versions.tf` (troué) et `main.tf` (fourni, deux ressources triviales) :

```hcl
terraform {
  required_version = ???        # un LITTERAL : le bloc terraform n'accepte pas de variable
  required_providers {
    local  = { source = "hashicorp/local", version = ??? }    # EPINGLER 2.5.1
    random = { source = "hashicorp/random", version = ??? }   # PESSIMISTE : 3.x, pas 4.0
  }
}
```

`terraform init` échoue en l'état : les `???` ne sont pas du HCL valide.

## L'état à atteindre

1. `required_version` est un **littéral** satisfait par Terraform 1.15 (par exemple `>= 1.15.0`). Une variable y lèverait `Variables not allowed`.
2. Le provider `local` est **épinglé exactement** à `2.5.1` : `terraform version -json` le montre résolu pile à cette version.
3. Le provider `random` est borné en **pessimiste** (`~> 3.6`) : il se résout dans la série `3.x`, jamais `4.0`.
4. Le lock file `.terraform.lock.hcl` est généré, avec des empreintes `h1:` pour les deux providers et la version `2.5.1` de local.
5. Le projet converge : `apply` réussit et un second plan ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant. Ils lisent `terraform version -json`, le lock file (un artefact généré) et des codes retour.

1. `terraform version -json` : `provider_selections` donne `registry.terraform.io/hashicorp/local` valant exactement `2.5.1`. Un pin différent se verrait.
2. Toujours dans `provider_selections`, `hashicorp/random` est en série `3.x` et au moins `3.6`.
3. `.terraform.lock.hcl` contient au moins deux empreintes `h1:` et la version `2.5.1`.
4. `terraform apply` réussit (le required_version littéral est satisfait), puis `terraform plan -detailed-exitcode` retourne 0.

Référence : https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/version-constraints-terraform/

## 🎯 Challenge : contraindre et verrouiller les versions

### Point de départ

`challenge/work` contient `versions.tf` (troué) et `main.tf` (fourni, deux
ressources triviales pour tirer les providers `local` et `random`).
`terraform init` échoue en l'état.

### ✅ Objectif

Complétez les trois contraintes de `versions.tf` :

1. **`required_version`** : un **littéral** contraignant Terraform à au moins
   `1.15.0` (par exemple `>= 1.15.0`). Le bloc `terraform` n'accepte **aucune**
   variable (`Variables not allowed`).
2. **`local`** : **épinglez exactement** la version `2.5.1` (opérateur `=`).
3. **`random`** : bornez en **pessimiste** pour autoriser toute la série `3.x`
   compatible (à partir de `3.6`) mais **jamais** `4.0` (`~> 3.6`).

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

### 🧭 Ce que le lab vous fait constater

- **Le pin exact `=`** fait résoudre `local` pile à `2.5.1`.
- **Le pessimiste `~>`** garde `random` dans la série `3.x`.
- **Le lock file** enregistre des empreintes `h1:` et se committe.

### 🔍 Validation

```bash
dsoxlab check write-code-version-constraints
```

Quatre tests lisant `terraform version -json`, le lock file et des codes retour :
le pin exact de `local`, le pessimiste de `random`, les empreintes `h1:` du lock,
et l'idempotence. Aucun ne lit vos `.tf`.
