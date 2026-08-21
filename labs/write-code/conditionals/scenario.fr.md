# Scénario : la configuration qui refuse les valeurs absurdes

**Sous-objectif d'examen visé : 2a (valider la configuration), avec un appui sur 2c pour les expressions conditionnelles.**

Le guide de référence n'enseigne qu'un des quatre mécanismes de validation de Terraform, le bloc `validation` des variables. Ce lab rétablit les quatre et fait porter la note sur ce qui les sépare : le moment où chacun s'exécute, et le fait qu'un seul d'entre eux avertit sans bloquer.

## Capacité visée

Rendre une configuration auto-défensive : calculer des valeurs par expression conditionnelle, puis empêcher qu'une valeur absurde arrive jusqu'à l'infrastructure, en plaçant chaque contrôle au bon niveau. Le piège central est de croire que `validation` suffit à tout : un bloc `validation` ne vit que sur une variable d'entrée et ne peut donc rien dire d'une valeur **calculée**. Contrôler le résultat d'un ternaire impose une `precondition`. Second piège : un `check` en échec n'arrête rien, il émet un avertissement et l'`apply` sort en code 0.

## D'où part l'apprenant

`challenge/work/` contient un projet incomplet, sans VM ni réseau : seul `hashicorp/local` est utilisé, avec un `terraform init` et un `.terraform.lock.hcl` déjà en place. `versions.tf` est correct et impose `required_version = ">= 1.9.0"`, version à partir de laquelle une condition de validation peut référencer une autre variable. `variables.tf`, `main.tf` et `outputs.tf` sont troués :

```hcl
variable "environment" { }          # string, default "dev", n'accepter que dev, staging, prod
variable "backup_bucket" { }        # string, default "", obligatoire SI environment vaut prod
variable "enable_second_disk" { }   # bool, default false
variable "memory_mib_override" { }  # number, nullable, default null
locals {
  memory_mib       = ???            # override sinon 2048 en prod, 512 sinon
  vcpu             = ???            # 4 en prod, 2 en staging, 1 sinon
  second_disk_name = ???            # "<nom>-data.qcow2" si le flag est vrai, null sinon
}
resource "local_file" "manifest" {
  filename = "${path.module}/manifest.json"
  content  = ???                    # JSON portant au moins env, memory_mib, vcpu
  lifecycle {
    precondition  { ??? }           # refuser moins de 256 MiB par vCPU
    postcondition { ??? }           # le contenu doit être du JSON portant une clé env
  }
}
check "budget_prod" { ??? }         # avertir si memory_mib dépasse 1024
```

`terraform plan` échoue en l'état : les `???` ne sont pas du HCL valide.

## L'état à atteindre

1. `environment` rejette toute valeur hors `dev`, `staging`, `prod`, avant même la génération du plan.
2. `backup_bucket` est refusé vide quand `environment` vaut `prod`, et accepté vide sinon : la condition référence une **autre** variable, ce qui exige Terraform 1.9 ou plus.
3. `local.memory_mib` vaut 512 en `dev`, 2048 en `prod`, et cède la place à `memory_mib_override` dès que celui ci n'est pas `null`. `local.vcpu` vaut 1, 2 ou 4 selon l'environnement.
4. `local.second_disk_name` vaut `null` quand le flag est faux. L'output correspondant **disparaît** alors, au lieu de valoir `null`.
5. La `precondition` de `local_file.manifest` bloque le plan dès que le rapport mémoire sur vCPU tombe sous 256 MiB, cas inatteignable par une `validation` puisque les deux termes sont des `locals`.
6. La `postcondition` relit `self.content` après écriture et exige un JSON portant une clé `env`.
7. Le bloc `check` est en échec en `prod` et c'est voulu : l'`apply` doit réussir malgré lui.
8. Le projet converge : un second plan juste après l'apply ne propose plus rien.

## Comment on le prouve

Les tests n'ouvrent jamais les `.tf` de l'apprenant et ne lisent aucun message humain. Ils lancent Terraform dans `challenge/work` et n'exploitent que du JSON et des codes retour.

1. `terraform show -json` après apply expose un tableau `checks` de premier niveau. Les tests y vérifient la présence de quatre adresses et leur `status` : `var.environment` et `var.backup_bucket` en `kind: var`, `local_file.manifest` en `kind: resource`, `check.budget_prod` en `kind: check`. Un `kind` manquant prouve un mécanisme non écrit.
2. `terraform plan -var 'environment=qa'` sort en code non nul. Idem pour `-var 'environment=prod' -var 'backup_bucket='`, alors que `-var 'environment=dev' -var 'backup_bucket='` sort en code 0 : la validation croisée est bien conditionnelle.
3. `terraform output -json` : `memory_mib` et `vcpu` valent le couple attendu pour chaque environnement testé.
4. `terraform output -json` avec `enable_second_disk=false` : la clé `second_disk_name` est **absente** du document. Le test échoue si la clé existe avec une valeur nulle. Avec `true`, la clé est présente et non vide.
5. `terraform plan -var 'memory_mib_override=64'` sort en code non nul, alors que la même valeur ne viole aucune contrainte de variable : seule une `precondition` peut produire ce refus.
6. `terraform show -json` : la ressource `local_file.manifest` est en `mode: managed`, et son attribut `content` se décode en JSON portant `env`, `memory_mib` et `vcpu`. La postcondition est donc satisfaite sur une donnée réellement écrite.
7. Marche décisive : `terraform apply -auto-approve -var 'environment=prod' -var 'backup_bucket=lab-backup'` sort en **code 0** pendant que `checks` marque `check.budget_prod` en `fail`. Bloquant et non bloquant sont séparés par la preuve, pas par la lecture.
8. `terraform plan -detailed-exitcode` retourne 0 juste après l'apply. Un code 2 fait échouer le lab, y compris quand le plan annonce zéro changement : placer une `data` source dans le bloc `check` la fait relire à chaque plan et suffit à ramener 2. L'assertion doit porter sur une valeur déjà connue.
