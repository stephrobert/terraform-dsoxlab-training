# Deux configurations, un state partagé, aucune interaction

Le troisième objectif du Professional est celui de l'équipe : verrouiller les
versions, partager l'état, s'exécuter sans qu'un humain confirme quoi que ce
soit. Ce capstone fait collaborer **deux configurations séparées**.

`reseau/` publie, `application/` consomme. Le lab se joue sur **Floci**, qui
fournit le backend S3 : aucun compte AWS, aucune facture.

## Aucune expression ne traverse la frontière

C'est la règle qui gouverne tout le reste. Deux configurations ne partagent ni
variables, ni locals, ni ressources. La **seule** passerelle est la lecture de
l'état distant, par ses **outputs déclarés** :

```hcl
data "terraform_remote_state" "reseau" {
  backend = "s3"
  config  = { bucket = "capstone3-etats", key = "reseau/terraform.tfstate", ... }
}
```

Conséquence directe : ce que l'amont n'expose pas en `output` est **invisible**
d'en face, même si la valeur figure dans son state. Les outputs d'une stack
partagée ne sont pas de la décoration, ce sont son **contrat**.

## Un bloc `backend` n'accepte aucune valeur nommée

```hcl
backend "s3" {
  bucket = var.backend_bucket   # Error: Variables not allowed
}
```

Le backend est résolu **avant** toute évaluation d'expression : il faut savoir où
lire l'état avant de pouvoir lire quoi que ce soit. C'est pour cela que la
configuration **partielle** existe :

```hcl
backend "s3" {}
```

```bash
terraform init -backend-config=backend.tfbackend
```

La forme fichier est préférable à `-backend-config="cle=valeur"`, que la
documentation déconseille pour un secret : l'historique du shell le conserve.

## Le cycle en deux temps, et ce qu'il ferme

```bash
terraform plan -out=tf.plan -input=false
terraform apply -input=false tf.plan
```

Un `apply` direct **relit la configuration** au moment d'appliquer. Entre la
revue et l'application, quelqu'un a pu pousser un commit : ce qui a été relu
n'est donc pas forcément ce qui part.

Appliquer un plan **enregistré** ferme cet écart. Et `-input=false` garantit
qu'aucune question n'attend une réponse que personne ne donnera : une CI qui
pose une question est une CI qui expire.

## La seule preuve qui vaille : changer l'amont

Tout le reste pourrait être obtenu en recopiant trois valeurs à la main. Le test
décisif rejoue `reseau/` avec une autre plage, puis exige que l'aval **suive** :

```console
$ cd reseau && terraform apply -var 'plage_reseau=10.77.0.0/16'
$ cd ../application && terraform plan -detailed-exitcode ; echo $?
2
```

Un `0` à cet endroit signifierait que l'aval ne lit rien : ses valeurs sont
figées. C'est exactement ce que ce test existe pour attraper.

## À vous de jouer

```bash
dsoxlab run certifications-professional-capstone3-collaborative-workflows
dsoxlab check certifications-professional-capstone3-collaborative-workflows
dsoxlab hint certifications-professional-capstone3-collaborative-workflows
```

Sept tests. Aucun ne lit vos `.tf` : le backend se prouve par l'absence de state
local et la présence des deux clés dans le bucket, la lecture distante par une
entrée `mode: data` de type `terraform_remote_state`, et les contraintes par le
verrou.

Objectif d'examen visé : **3**, dans ses quatre sous-objectifs.

Référence : [le programme du Terraform Authoring and Operations Professional](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
