# Scénario : la valeur qui gagne

**Sous-objectif d'examen visé : 2e (déclarer et consommer variables et outputs, y compris les types complexes et la précédence des valeurs).**

Une même variable est renseignée par cinq sources qui se contredisent. L'apprenant doit rendre le projet capable de dire laquelle l'emporte, et le prouver sans relire une ligne de HCL.

## Capacité visée

Paramétrer une configuration Terraform avec des variables typées, dont une de type complexe, contraindre leurs valeurs par un bloc `validation`, exposer les résultats par des `output`, et prédire la valeur effectivement retenue quand `default`, `TF_VAR_*`, `terraform.tfvars`, `env.auto.tfvars` et `-var` entrent en conflit. Le piège est le rang réel de `TF_VAR_*` : il se situe juste au dessus du `default`, donc **en dessous** de tous les fichiers de valeurs, à l'inverse de l'intuition « une variable d'environnement écrase un fichier ».

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet. Aucune VM, aucun provider distant : seuls `hashicorp/local` et `hashicorp/random` sont utilisés, avec un `terraform init` et un `.terraform.lock.hcl` déjà en place. Le lab tourne partout où `terraform` est sur le PATH, sans réseau.

Le répertoire contient `versions.tf` (déjà correct), `variables.tf`, `locals.tf`, `main.tf`, `outputs.tf` et un `terraform.tfvars` qui fixe `env` et reste muet sur `region`. Tout le reste est troué :

```hcl
variable "env" {          # string, default "dev"
  type       = ???
  validation {            # n'accepter que dev, staging, prod
    condition     = ???
    error_message = "???"
  }
}
variable "replicas" { ??? }  # number, default 2, plage 1 à 9
variable "sizing"   { ??? }  # object({ cpu = number, memory_mb = number })
variable "region"   { ??? }  # string, SANS default : TF_VAR_ ou -var
```

`terraform plan` échoue en l'état : les `???` ne sont pas du HCL valide.

## L'état à atteindre

1. Les quatre variables sont typées et décrites. `sizing` est un `object({ cpu = number, memory_mb = number })` avec un `default`.
2. `env` rejette toute valeur hors `dev`, `staging`, `prod`. `replicas` rejette hors 1 à 9. Chaque bloc `validation` porte son `error_message`, qui est obligatoire.
3. `terraform.tfvars` fixe `env = "staging"` et ne dit rien de `region`.
4. Un fichier `env.auto.tfvars` fixe `env = "prod"`, chargé automatiquement.
5. `local.stack_name` vaut `app-<env>-<region>`, calculé en interne, jamais fourni de l'extérieur.
6. `main.tf` écrit `manifest-<stack_name>.json` via `local_file`.
7. `outputs.tf` expose `env_effectif`, `region_effective`, `stack_name`, `sizing_total_mb` (mémoire multipliée par les replicas) et `manifest_path`.
8. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne parsent aucun message d'erreur humain. Ils lancent Terraform dans `challenge/work` et ne lisent que du JSON ou des codes retour.

1. `TF_VAR_region=eu-west-1 terraform apply -auto-approve` puis `terraform output -json` : `region_effective` vaut `eu-west-1`. `TF_VAR_*` couvre bien une variable sans `default`.
2. Avec `env.auto.tfvars` écarté, `TF_VAR_env=dev terraform apply -auto-approve` puis `terraform output -json` : `env_effectif` vaut `staging`. **Le fichier `terraform.tfvars` bat la variable d'environnement**, marche décisive du lab.
3. `env.auto.tfvars` remis en place, même commande : `env_effectif` vaut `prod`. Le fichier `auto` bat `terraform.tfvars`.
4. `terraform apply -var 'env=dev' -auto-approve` : `env_effectif` vaut `dev`. Le flag bat tout le reste. Les quatre marches sont vérifiées dans l'ordre.
5. `terraform output -json` : `sizing_total_mb` est un nombre égal à `memory_mb` multiplié par `replicas`, ce qui prouve que le type complexe est réellement consommé.
6. `terraform plan -var 'env=qa'` sort avec un code retour non nul, `terraform plan -var 'replicas=0'` aussi. Seul le code retour est vérifié.
7. `terraform show -json` : une ressource `local_file` existe et son chemin contient le `stack_name` attendu.
8. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply. Un code 2 fait échouer le lab.
