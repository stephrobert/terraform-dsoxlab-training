# Scénario : un backend, deux environnements, zéro chemin en dur

**Sous-objectif d'examen visé : 3b (remote state).**

Le bloc `backend` n'accepte **aucune valeur nommée** : ni variable, ni local, ni attribut de data source. C'est le piège de ce lab, et la raison d'être de la **configuration partielle** et de `-backend-config`.

## Capacité visée

Configurer un backend en **configuration partielle** (le bloc ne fixe aucun `path`), l'alimenter par un fichier `-backend-config` distinct par environnement, et faire **migrer** un state existant vers ce backend **sans le recréer**.

## D'où part l'apprenant

`challenge/work` contient un projet appliquable, en fichiers de premier niveau (le runtime aplatit les sous-dossiers) :

- `versions.tf`, `main.tf` : complets, à ne pas modifier. `main.tf` a un `random_pet` et un `local_file`, dont le state doit migrer.
- `variables.tf` : une variable `chemin_state` déclarée, le **piège** : s'en servir dans le bloc backend fait échouer `init` sur `Variables not allowed`.
- `dev.local.tfbackend` : une ligne, `path = "???"`.
- `backend.tf` et `prod.local.tfbackend` : **absents**, à créer.

Le test **orchestre** la migration comme le ferait un vrai passage au backend : il applique d'abord avec le **backend local implicite** (sans `backend.tf`), capture le `lineage`, puis ajoute `backend.tf` et lance `terraform init -migrate-state -backend-config=dev.local.tfbackend`.

## L'état à atteindre

1. Un bloc `backend "local"` existe et ne fixe **aucun** `path` : réinitialisé sans `-backend-config`, Terraform résout `path` à `null`.
2. Deux configurations partielles désignent deux emplacements : `etat/dev/terraform.tfstate` et `etat/prod/terraform.tfstate`.
3. Après migration sur `dev`, le backend retenu est de type `local` et sa `path` résolue est celle de `dev`.
4. Le state a **migré**, il n'a pas été recréé : **même `lineage`** qu'au départ, et les deux ressources en `mode: managed`.
5. `etat/dev/terraform.tfstate` existe sur le disque.
6. Aucun changement en attente : `plan -detailed-exitcode` rend `0`.

## Comment on le prouve

Les tests n'ouvrent jamais un `.tf`. Ils lisent ce que Terraform écrit.

1. **Migration, pas recréation** : `terraform state pull` avant et après ; le `lineage` est **identique**. Un `apply` refait de zéro produirait un lineage neuf et tomberait ici. `show -json` liste exactement deux ressources `mode: managed`.
2. **Backend résolu** : `.terraform/terraform.tfstate` porte `backend.type = local` et `backend.config.path = etat/dev/terraform.tfstate`. Son absence prouverait un backend resté implicite.
3. **Config partielle** : dans une **copie** du dossier, `terraform init` **sans** `-backend-config` résout `path` à `null` (un chemin codé en dur ressortirait ici), et `init -reconfigure -backend-config=prod.local.tfbackend` résout sur `etat/prod`. Le même bloc, deux emplacements : c'est la preuve du caractère partiel.
4. **Idempotence** : `plan -detailed-exitcode` rend `0`.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/backends-terraform/
