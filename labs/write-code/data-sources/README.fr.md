# À quel moment Terraform lit-il une data source ?

Écrire un bloc `data` est trivial. Savoir **quand** Terraform le lit l'est
beaucoup moins, et c'est pourtant ce qui explique deux situations frustrantes :
un plan qui affiche `(known after apply)` là où vous attendiez une valeur, et un
plan qui annonce des changements alors qu'aucune ligne de HCL n'a bougé.

Ce tutoriel enseigne le mécanisme sur un exemple **jetable** : une station météo
qui lit des seuils et produit des relevés. Rien à voir avec le challenge, qui
vous demandera d'appliquer ces mêmes idées à un autre cas. Tout tourne sur
`local` et `random`, sans cloud ni VM.

## Monter l'exemple

Créez un répertoire à part, hors du challenge, avec un fichier `seuils.txt` et
un `main.tf` :

```text
seuil_alerte=38
station=eu-nord
```

```hcl
variable "cycle" {
  type    = number
  default = 1
}

resource "random_pet" "station" {
  length  = 2
  keepers = { cycle = var.cycle }
}

resource "local_file" "releve" {
  filename = "${path.module}/out/releve-${random_pet.station.id}.txt"
  content  = "cycle=${var.cycle}\n"
}
```

Vous ajouterez les data sources au fil des sections. Lancez d'abord
`terraform init` puis `terraform apply` pour partir d'un état stable.

## Une lecture qui reste connue au plan

Ajoutez une data source dont l'argument ne dépend d'aucune ressource, seulement
d'un chemin :

```hcl
data "local_file" "seuils" {
  filename = "${path.module}/seuils.txt"
}
```

Après un `apply`, demandez au plan quelles data sources il compte lire :

```bash
terraform plan -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | select(.mode == "data")'
```

La sortie est vide. C'est le signe que la lecture a **déjà eu lieu pendant le
plan** : il n'y a rien à planifier. Vous la retrouvez, avec ses valeurs réelles,
dans l'état antérieur :

```bash
terraform show -json tf.plan | jq '.prior_state.values.root_module.resources[].address'
```

```text
"data.local_file.seuils"
"local_file.releve"
"random_pet.station"
```

Toute la suite repose sur cette opposition : lue au plan, une data source est
dans `prior_state` et absente de `resource_changes`.

## Une lecture qui se décale à l'apply

Ajoutez maintenant une data source qui relit le fichier **produit** par
`local_file.releve`, en référençant son attribut. C'est la référence qui crée la
dépendance, ne recopiez pas le chemin à la main :

```hcl
data "local_file" "releve_relue" {
  filename = local_file.releve.filename
}
```

Faites bouger la ressource gérée en changeant `cycle`, et regardez les data
sources du plan :

```bash
terraform apply -auto-approve
terraform plan -var 'cycle=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.mode == "data") | {address, actions: .change.actions}'
```

```text
{"address":"data.local_file.releve_relue","actions":["read"]}
```

La lecture est reportée à l'apply : elle apparaît cette fois dans
`resource_changes`, avec `mode: data` et `actions: ["read"]`. Terraform ne peut
pas la lire au plan, puisque le fichier visé n'a pas encore son nom définitif.
Relancez la même commande sans `-var 'cycle=2'` et la sortie redevient vide : le
même bloc bascule d'un cas à l'autre selon l'état de sa dépendance, sans qu'une
ligne change.

## depends_on ne décale rien

C'est la croyance qu'il faut casser, et le cœur du challenge à venir. Ajoutez une
troisième data source qui lit le même `seuils.txt`, avec en plus une dépendance
explicite :

```hcl
data "local_file" "seuils_ordonnes" {
  filename   = "${path.module}/seuils.txt"
  depends_on = [random_pet.station]
}
```

Avec tout stable, comptez les data sources reportées :

```bash
terraform apply -auto-approve
terraform plan -out=tf.plan
terraform show -json tf.plan | jq '[.resource_changes[] | select(.mode == "data")] | length'
```

```text
0
```

Malgré son `depends_on`, cette data source est lue au plan, exactement comme la
première. Beaucoup de tutoriels affirment le contraire. Faites bouger la
ressource visée, et elle rejoint les reportées :

```bash
terraform plan -var 'cycle=2' -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | select(.mode == "data") | .address'
```

```text
"data.local_file.releve_relue"
"data.local_file.seuils_ordonnes"
```

Ce n'est donc pas `depends_on` qui décide du report, mais le fait que la
ressource visée soit **configurée pour changer dans le plan courant**.

## D'où vient le (known after apply)

Exposez les deux lectures dans des outputs :

```hcl
output "seuils" {
  value = data.local_file.seuils.content
}

output "releve" {
  value = data.local_file.releve_relue.content
}
```

Un output qui dérive d'une lecture reportée ne peut pas être connu au plan. Le
champ `after_unknown` le confirme :

```bash
terraform apply -auto-approve
terraform plan -var 'cycle=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.output_changes | map_values(.after_unknown)'
```

```text
{"releve":true,"seuils":false}
```

`releve` porte `after_unknown: true` : c'est l'origine exacte du
`(known after apply)` que vous lisez dans le plan en clair. `seuils`, dont la
source est lue au plan, reste connu.

## La dérive qui ne vient pas de votre code

Cette conséquence surprend toujours. Sans toucher un seul `.tf`, modifiez le
fichier lu :

```bash
terraform apply -auto-approve
terraform plan -detailed-exitcode ; echo "code = $?"
```

```text
code = 0
```

```bash
echo "seuil_max=45" >> seuils.txt
terraform plan -detailed-exitcode ; echo "code = $?"
```

```text
code = 2
```

Le code `2` signale des changements planifiés. Une data source est relue à chaque
plan, et c'est cette lecture fraîche, non une valeur conservée dans l'état, qui
alimente le diff.

## Ce que devient une data source au destroy

Terraform ne détruit pas ce qu'il n'a jamais créé. Le plan de destruction ignore
les data sources :

```bash
terraform plan -destroy -out=tf.plan
terraform show -json tf.plan | jq '[.resource_changes[] | select(.mode == "data")] | length'
```

```text
0
```

Allez au bout, la nuance compte. Appliquez ce plan, puis listez l'état :

```bash
terraform apply -auto-approve tf.plan
terraform state list
```

La sortie est vide. Les data resources ont disparu de l'état avec le reste :
elles ne sont pas détruites, elles cessent simplement d'exister. Dire qu'une data
source « survit » à un destroy serait donc faux.

## À vous de jouer

Vous savez maintenant lire le moment d'une data source dans le plan JSON. Le
challenge applique tout cela à un autre décor, et vérifie chaque cas :

```bash
dsoxlab run write-code-data-sources
dsoxlab check write-code-data-sources
dsoxlab hint write-code-data-sources
```

Gardez en tête la seule question qui compte : le critère de report n'est jamais
« cette data source a une dépendance », mais « la ressource dont elle dépend
change-t-elle dans ce plan ? ».

Sous-objectif d'examen visé : **2b** (Terraform Authoring and Operations
Professional).

Référence : [Les data sources Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/data-sources/)
