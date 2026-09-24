# Variables, locals et l'ordre de précédence réel

Une variable Terraform peut recevoir sa valeur de cinq endroits différents. Tant
qu'un seul parle, tout va bien. Le jour où deux se contredisent, il faut savoir
lequel gagne, et l'intuition se trompe à un endroit précis qui coûte une soirée.

Ce lab se joue **hors ligne**, sur les providers `local` et `random` : aucune
VM, aucun compte, et pourtant tout ce qui compte s'y observe.

## Les cinq marches, dans l'ordre

```text
default  <  TF_VAR_  <  terraform.tfvars  <  *.auto.tfvars  <  -var
```

La marche **décisive** est la deuxième : un simple fichier de valeurs **bat** la
variable d'environnement. `TF_VAR_` se situe juste au-dessus du `default`, et
en dessous de **tout** fichier.

C'est le rang que presque tout le monde place trop haut, parce que ailleurs
qu'ici, une variable d'environnement est un moyen d'écraser une configuration.
Chez Terraform, c'est l'inverse : elle est ce qu'on fournit quand aucun fichier
ne parle.

La plus **discrète** est la troisième. Un fichier `*.auto.tfvars` est chargé
automatiquement, après `terraform.tfvars`. Son nom ne le dit pas, aucune
commande ne le mentionne, et le collègue qui en dépose un dans le dépôt change
le comportement de tout le monde sans qu'une ligne de code ait bougé.

## Une variable sans `default` n'est pas une variable manquante

`region` n'a pas de `default`, et cela ne rend pas la configuration invalide :
cela rend la valeur **obligatoire**. Terraform la demandera en interactif, ou la
prendra dans `TF_VAR_region`, ou dans un `-var`.

C'est la bonne façon de déclarer ce qui n'a pas de valeur raisonnable par
défaut. Un `default = ""` posé pour faire taire l'outil transforme une erreur
franche en configuration silencieusement fausse.

## `validation` juge une valeur, pas une frappe

```hcl
variable "replicas" {
  type    = number
  default = 2

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 9
    error_message = "replicas doit rester entre 1 et 9."
  }
}
```

Deux choses à savoir :

- **`error_message` est obligatoire.** Un bloc `validation` sans message ne
  compile pas ;
- **le refus arrive au plan**, pas à l'apply. C'est ce qui en fait un garde-fou
  utile : la valeur absurde est rejetée avant que quoi que ce soit n'existe.

Les tests du lab jugent ces validations sur le **code retour seulement**. Un
message est une chaîne que son auteur choisit ; en faire un critère reviendrait
à noter la rédaction. Et un contre-contrôle vérifie qu'une valeur **admise**
passe, sans quoi une condition qui refuse tout ferait passer le test pour la
mauvaise raison.

## Un type complexe se prouve en le consommant

```hcl
variable "sizing" {
  type = object({
    cpu       = number
    memory_mb = number
  })
  default = { cpu = 2, memory_mb = 2048 }
}
```

Déclarer l'objet ne prouve rien : un `any` passerait aussi. Ce qui prouve que le
type est réellement tenu, c'est un output qui **calcule** avec ses champs :

```hcl
output "sizing_total_mb" {
  value = var.sizing.memory_mb * var.replicas
}
```

Si le champ n'existait pas, ou n'était pas un nombre, l'expression tomberait.

## Un local n'est pas une variable

`local.stack_name` vaut `app-<env>-<region>`. La différence tient en une phrase :
une **variable** est une entrée du projet, un **local** est un calcul interne.
Personne ne peut fournir un local depuis l'extérieur, et c'est précisément ce
qu'on veut pour une valeur dérivée : elle ne peut pas diverger de ce dont elle
dérive.

## À vous de jouer

```bash
dsoxlab run first-infra-variables-outputs
dsoxlab check first-infra-variables-outputs
dsoxlab hint first-infra-variables-outputs
```

Huit tests. Les quatre marches sont vérifiées **dans l'ordre**, en manipulant
réellement l'environnement et les fichiers, jamais en relisant votre HCL.

Sous-objectif d'examen visé : **2e**.

Référence : [variables et outputs](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/variables-outputs/)
