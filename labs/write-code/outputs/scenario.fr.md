# Scénario : le secret que l'output ne cache pas

**Sous-objectif d'examen visé : 2f (gérer les données sensibles), en appui sur 2e (déclarer variables et outputs, types complexes).**

Un mot de passe généré par Terraform doit sortir du projet, mais sans finir en clair là où on ne l'attend pas. L'apprenant doit démontrer, mesures à l'appui, ce que `sensitive = true` masque vraiment et ce qu'il ne masque pas, exposer une empreinte sans divulguer le secret, et verrouiller son module par un `precondition` porté par un output.

## Capacité visée

Exposer les résultats d'une configuration en maîtrisant les arguments réels du bloc `output` : `value`, `type` (contrainte de type, Terraform 1.15), `sensitive`, et `precondition`. Savoir que la sensibilité **se propage**, y compris à travers une fonction : le `sha256` d'un secret reste sensible, et l'exposer suppose une déclassification explicite par `nonsensitive()`. Savoir surtout que `sensitive` n'agit que sur l'affichage : la valeur reste en clair dans le state, dans `terraform output -json` et dans `terraform output -raw`.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet. Aucune VM, aucun compte distant : seuls `hashicorp/random` et `hashicorp/local` sont utilisés, `terraform init` est déjà passé et `.terraform.lock.hcl` est en place. Le lab tourne partout où `terraform` 1.15 ou plus est sur le PATH, sans réseau.

Le répertoire contient `versions.tf` (déjà correct, `required_version = ">= 1.15.0"`), `variables.tf` avec `longueur_mot_de_passe` (number, défaut 24), `main.tf` (fourni) qui déclare `random_password.admin` et un `local_file.rapport` **non secret** (il n'écrit que la longueur), et un `outputs.tf` troué :

```hcl
output "mot_de_passe_admin" {   # type string, VALEUR SENSIBLE
  ???
}
output "resume" {               # object({ longueur = number, empreinte = string })
  ???                           # empreinte = sha256 du secret, mais SANS le divulguer
}
output "empreinte_rapport" {    # sha256 du contenu du rapport
  value = sha256(local_file.rapport.content)
  ???                           # un precondition a ecrire
}
```

`terraform plan` échoue en l'état : les `???` ne sont pas du HCL valide, et un output référençant le secret sans `sensitive` serait de toute façon refusé.

## L'état à atteindre

1. `mot_de_passe_admin` porte `type = string`, `sensitive = true` et expose `random_password.admin.result`. Sans `sensitive`, le plan est refusé (« Output refers to sensitive values »).
2. `resume` porte la contrainte `type = object({ longueur = number, empreinte = string })` et n'est **pas** sensible. `empreinte` est le `sha256` du mot de passe, mais comme le `sha256` d'un secret reste sensible, l'apprenant doit le déclassifier par `nonsensitive()`. Aucune valeur de l'objet n'est le secret.
3. `empreinte_rapport` porte un bloc `precondition` avec son `error_message` obligatoire, qui exige `var.longueur_mot_de_passe >= 20`.
4. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne parsent aucune sortie humaine. Ils lancent Terraform dans `challenge/work` et ne lisent que du JSON ou des codes retour.

1. `terraform output -json` : `mot_de_passe_admin` a `"sensitive": true` et son champ `value` contient la chaîne **en clair**, de longueur 24. C'est la démonstration centrale du lab.
2. `terraform show -json` : `random_password.admin` expose sous `values.result` exactement la même chaîne. Le state conserve le secret en clair, `sensitive` ou non.
3. `terraform output -raw mot_de_passe_admin` renvoie la même chaîne : `-raw` lève la redaction au même titre que `-json`.
4. Dans `terraform output -json`, `resume` n'est pas sensible, c'est un objet à clés `longueur` (valant 24) et `empreinte` (64 caractères hexadécimaux), et aucune valeur de l'objet n'égale le mot de passe.
5. `empreinte_rapport` est un `sha256` de 64 caractères.
6. `terraform plan -var 'longueur_mot_de_passe=8'` sort avec un code retour non nul : le `precondition` de l'output bloque le plan.
7. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply. Un code 2 fait échouer le lab.

Référence : https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/outputs-terraform/
