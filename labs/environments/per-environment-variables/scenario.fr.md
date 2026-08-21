# Scénario : la valeur qui gagne, et pourquoi

**Sous-objectif d'examen visé : 2e.**

Découper les valeurs par environnement dans des fichiers `.tfvars` est facile ; savoir laquelle de six sources concurrentes finit dans le plan l'est beaucoup moins. Le lab traite l'échelle de précédence complète, y compris les deux marches que la plupart des tutoriels ratent : les variables d'environnement `TF_VAR_`, absentes des tableaux, et le fait que `-var` et `-var-file` sont au **même** niveau, départagés par l'ordre des arguments et non par une hiérarchie.

## Capacité visée

Paramétrer une configuration unique pour trois environnements avec des fichiers de valeurs, puis prédire et démontrer, pour une variable donnée, quelle source l'emporte parmi le `default`, une variable d'environnement, `terraform.tfvars`, un `*.auto.tfvars` et les options de la ligne de commande.

## D'où part l'apprenant

`challenge/work` contient une configuration ni initialisée ni appliquée, limitée aux providers `hashicorp/local` et `hashicorp/random` :

- `versions.tf` : complet, à ne pas toucher. `required_version = ">= 1.15.0"`, les deux providers épinglés.
- `variables.tf` : `env_name` et `disk_size_gb` sans `default` (le garde fou), `retention_jours` avec un `default`, `base_image` et `tags` amorcés avec des `???` sur le type.
- `main.tf` : `local_file.profil` écrit un `jsonencode` des valeurs résolues dans `profils/${var.env_name}.json`, et `random_pet.suffixe` porte l'environnement dans son `keepers`. Les deux blocs sont troués par des `???`.
- `outputs.tf` : `profil` et `taille_octets` amorcés, expressions à écrire.
- `terraform.tfvars` **présent à la racine** et porteur de `env_name = "bac-a-sable"` et `disk_size_gb = 1`. Il neutralise silencieusement le garde fou : `terraform plan -input=false` réussit alors qu'aucun environnement n'a été choisi. C'est le constat de départ, pas une faute de frappe.
- `commun.auto.tfvars` : valeurs partagées (`base_image`, `tags`).
- `envs/dev.tfvars` complet, `envs/staging.tfvars` porteur d'une clé mal orthographiée (`disk_size_go`), `envs/prod.tfvars` incomplet.

## L'état à atteindre

1. `terraform validate -json` renvoie `valid: true` et `terraform plan -input=false`, sans aucune option de variables, **échoue** sur « No value for required variable » pour `env_name` : plus aucune source implicite ne fournit une valeur d'environnement.
2. Les valeurs réellement partagées (image de base, tags) restent chargées automatiquement, sans être répétées dans les trois fichiers d'environnement.
3. `envs/staging.tfvars` ne déclenche plus aucun avertissement de variable non déclarée : la clé mal orthographiée est corrigée, pas contournée par un `default`.
4. Les trois environnements se déploient depuis la même configuration : dev en 4 Go et 7 jours de rétention, staging en 4 Go et 14 jours, prod en 8 Go et 90 jours, chacun avec son propre nom de fichier de profil.
5. Avec `TF_VAR_env_name` exporté **et** `-var-file=envs/prod.tfvars`, la valeur retenue est `prod` : la variable d'environnement perd contre un fichier de valeurs.
6. Avec `TF_VAR_env_name` exporté seul, la valeur retenue est celle de l'environnement : elle bat le `default`, et le plan ne demande plus rien.
7. `terraform plan -var 'disk_size_gb=16' -var-file=envs/prod.tfvars` retient **8**, et `terraform plan -var-file=envs/prod.tfvars -var 'disk_size_gb=16'` retient **16**. Le même couple d'options, deux résultats : c'est l'ordre qui tranche.
8. Un second fichier auto chargé, lexicalement postérieur à `commun.auto.tfvars`, l'emporte sur lui pour la variable qu'ils partagent.
9. Le `tags` de la configuration est un type complexe passable en `-var` avec une syntaxe JSON, et la surcharge est effective.
10. Après l'apply de prod, un plan relancé ne propose plus rien.

## Comment on le prouve

Les tests pilotent Terraform et ne lisent jamais les fichiers `.tf` ni les `.tfvars` de l'apprenant.

- **Valeurs résolues** : `terraform plan -out=tfplan` puis `terraform show -json tfplan` ; la clé `variables` de la représentation JSON du plan expose la valeur retenue pour chaque variable racine. C'est la seule preuve recevable de précédence, et elle ne nécessite aucun apply.
- **Garde fou** : `terraform plan -input=false` sans option renvoie un code de sortie non nul, et `terraform plan -json` porte un diagnostic de sévérité `error` mentionnant `env_name`. Sur l'état de départ, le même appel réussit.
- **Variable non déclarée** : `terraform plan -json -var-file=envs/staging.tfvars` ne contient plus aucun diagnostic de sévérité `warning`. Sur l'état de départ, ce diagnostic existe.
- **Précédence `TF_VAR_`** : les tests recopient le workdir et son `.terraform` dans un répertoire temporaire, injectent `TF_VAR_env_name` dans l'environnement du processus, et comparent les deux plans, avec puis sans `-var-file`.
- **Ordre des options** : deux plans successifs avec les mêmes options dans les deux ordres, et deux valeurs de `disk_size_gb` différentes dans le JSON du plan. Une configuration qui figerait la taille ne peut pas produire ces deux valeurs.
- **Ordre lexical** : ajout d'un fichier auto chargé au nom lexicalement supérieur, et lecture de la variable partagée dans le JSON du plan.
- **État appliqué** : `terraform show -json` ; `local_file.profil` est en `mode: "managed"`, son `values.filename` porte le nom de l'environnement, et son `values.content` se parse en JSON pour comparer les valeurs résolues. `terraform output -json` confirme `profil` et `taille_octets`.
- **Idempotence** : `terraform plan -detailed-exitcode` renvoie 0 juste après l'apply de prod.

Aucun de ces contrôles ne passe sur un `challenge/work` vide : le premier plan n'y trouve aucune variable ni aucune ressource.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/variables-par-environnement/
