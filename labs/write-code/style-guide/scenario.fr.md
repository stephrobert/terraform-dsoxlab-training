# Scénario : la configuration qui marche mais qu'aucune CI n'accepte

**Sous-objectif d'examen visé : 2a (valider la configuration), avec un débord assumé sur 2e pour le typage des variables et des outputs.**

Un style guide ne se relit pas, il se fait rejeter par une CI. Ce lab traite le piège inverse du guide : les noms de fichiers ne changent rien au comportement de Terraform, donc les vérifier ne prouve rien. Ce qui prouve, c'est le code retour de `terraform fmt -check` et le JSON de `terraform validate`.

## Capacité visée

Reprendre une configuration Terraform fonctionnelle mais non conforme, la rendre conforme à `terraform fmt`, corriger l'incohérence interne qui fait échouer `terraform validate`, renommer les ressources selon la convention officielle, typer et documenter variables et outputs, marquer les valeurs sensibles, et poser un `.gitignore` correct, sans changer une seule des ressources créées.

## D'où part l'apprenant

`challenge/work/` contient un projet en un seul fichier, `infra.tf`. Aucune VM, aucun compte distant : seuls `hashicorp/local` et `hashicorp/random` sont utilisés, avec `terraform init` déjà en place. Le lab tourne partout où `terraform` est sur le PATH, sans réseau.

Le fichier est volontairement dégradé sur cinq axes à la fois :

- **Formatage** : indentation à quatre espaces, `=` non alignés. `terraform fmt -check` sort en code 3.
- **Cohérence** : le `content` du fichier généré référence `var.env_name`, une variable jamais déclarée (la variable existante s'appelle `environment`). `terraform validate` échoue et `terraform plan` refuse de démarrer.
- **Nommage** : les ressources s'appellent `local_file.localFileAppConfig` et `random_pet.randomPetInstanceName`, en camelCase et en répétant le type que l'adresse porte déjà.
- **Typage** : les variables `app_name`, `environment`, `replica_count` et `api_token` n'ont ni `type` ni `description`. Le `terraform.tfvars` fourni pose `replica_count = "3"`, avec les guillemets, ce qui passe silencieusement tant que la variable n'est pas typée.
- **Sensibilité et documentation** : aucun output ne porte de `description`, et l'output qui expose `var.api_token` n'est pas marqué `sensitive`.

Il n'y a ni `.gitignore` ni découpage.

## L'état à atteindre

1. `terraform fmt -check -recursive` ne signale plus rien.
2. `terraform validate` déclare la configuration valide : la référence orpheline `var.env_name` est résolue (en utilisant la variable existante `environment`, ou en déclarant celle qui manque).
3. La configuration crée toujours exactement les mêmes ressources : un `local_file` et un `random_pet`, ni plus ni moins.
4. Les adresses de ces ressources respectent la convention officielle : nom en snake_case, descriptif, sans répéter le type. Aucune majuscule, aucun tiret.
5. Toute variable porte une `description` non vide.
6. `replica_count` est réellement typée `number` : une valeur non numérique passée en `-var` est refusée, ce qu'une variable non typée accepterait.
7. Tout output porte une `description` non vide, et l'output qui expose le jeton d'API est marqué `sensitive`.
8. L'output qui expose le nombre de replicas est déclaré `type = number`, ce que la 1.15 recommande désormais : sa valeur ressort en nombre JSON alors que le `terraform.tfvars` la fournit entre guillemets.
9. Un `.gitignore` exclut `.terraform/`, `terraform.tfstate*` et les `.tfvars`, mais **n'**ignore **pas** `.terraform.lock.hcl` (à committer). Le motif `.terraform*` serait donc une erreur : il faut `.terraform/`.
10. Le projet converge : un second plan juste après l'apply ne propose plus rien.

Le style guide officiel recommande en outre de **découper** ce fichier unique en `terraform.tf`, `providers.tf`, `variables.tf`, `main.tf` et `outputs.tf` : c'est la bonne pratique enseignée, et l'apprenant est invité à le faire, mais le contrôle automatique porte sur les invariants ci-dessus, indépendants de la découpe.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant pour les parser. Ils lancent Terraform dans `challenge/work` et ne lisent que du JSON, des codes retour, et le `.gitignore` (un livrable, pas du HCL).

1. `terraform fmt -check -recursive` retourne 0.
2. `terraform validate -json` renvoie `valid: true`.
3. `terraform show -json` contient exactement un `local_file` et un `random_pet`.
4. Le champ `name` de chaque ressource respecte `^[a-z][a-z0-9_]*$`.
5. Le plan JSON (`configuration.root_module.variables`) donne une `description` non vide pour chaque variable.
6. `terraform plan -var replica_count=abc` sort en code non nul.
7. `terraform output -json` marque `api_token` sensible ; `replicas` a `type: number` et `value: 3` ; le plan JSON donne une `description` à chaque output.
8. Le `.gitignore` ignore `.terraform/` et `terraform.tfstate*`, et aucun motif n'ignore `.terraform.lock.hcl`.
9. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/style-guide-terraform/
