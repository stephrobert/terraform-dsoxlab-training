# Cesser de gérer une ressource, sans la détruire

Une ressource change de main : elle passe à une autre équipe, à un autre dépôt,
à un outil qui n'est pas Terraform. L'objet doit continuer d'exister, mais
Terraform doit arrêter de le suivre. C'est un besoin banal, et c'est aussi
l'opération la plus dangereuse du state : selon le mécanisme choisi, la même
intention conserve l'objet ou le supprime.

Deux voies existent. `terraform state rm` retire une entrée du state, tout de
suite, depuis votre poste. Le bloc `removed`, disponible depuis Terraform
**1.7**, déclare le retrait dans le code. Ce tutoriel les montre toutes les deux
sur une configuration jetable, avant que le challenge ne vous les fasse employer
chacune à sa place.

## Le terrain d'essai

Créez un répertoire à part, hors du challenge, avec cette configuration :

```hcl
terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

resource "local_file" "meteo" {
  filename = "${path.root}/meteo.csv"
  content  = "ville,temp\nlille,12\n"
}

resource "local_file" "lot" {
  count    = 3
  filename = "${path.root}/lot-${count.index}.txt"
  content  = "lot ${count.index}\n"
}

resource "random_pet" "demo" {
  length = 2
}
```

Un `terraform init` puis un `terraform apply` posent cinq objets, que le state
liste par leur adresse :

```bash
terraform state list
```

```text
local_file.lot[0]
local_file.lot[1]
local_file.lot[2]
local_file.meteo
random_pet.demo
```

## `terraform state rm` : l'oubli immédiat

La commande retire une entrée du state et **ne touche jamais** à l'objet réel.
Elle s'essaie d'abord à blanc, ce qui est une bonne habitude sur un state
partagé :

```bash
terraform state rm -dry-run local_file.meteo
```

```text
Would remove local_file.meteo
```

Puis pour de vrai :

```bash
terraform state rm local_file.meteo
```

```text
Removed local_file.meteo
Successfully removed 1 resource instance(s).
```

Le fichier, lui, est toujours là avec son contenu d'origine : `cat meteo.csv`
rend bien `ville,temp` puis `lille,12`. Terraform a simplement cessé de connaître
cet objet.

La signature accepte **plusieurs adresses** en un seul appel, et elle descend
jusqu'à **l'instance** quand la ressource porte un `count` ou un `for_each` :

```bash
terraform state rm 'local_file.lot[0]' 'local_file.lot[2]'
```

```text
Removed local_file.lot[0]
Removed local_file.lot[2]
Successfully removed 2 resource instance(s).
```

Les crochets se quotent, sous zsh comme sous bash : sans guillemets, le shell
essaie de les interpréter comme un motif et la commande ne reçoit jamais
l'adresse. Une adresse qui ne correspond à rien n'est pas silencieuse, elle sort
en **code 1** :

```text
Error: Invalid target address

No matching objects found. To view the available instances, use "terraform
state list". Please modify the address to reference a specific instance.
```

## L'orpheline : le piège du retrait impératif

Le retrait est fait, mais le bloc `resource` est toujours dans le code. Pour
Terraform, la lecture est sans ambiguïté : la configuration décrit un objet que
le state ne connaît pas, donc il faut le créer.

```bash
terraform plan
```

```text
  # local_file.meteo will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

C'est le piège de la voie impérative, et il est d'autant plus vicieux sur une
vraie infrastructure : le prochain `apply`, lancé par n'importe qui, recrée un
objet qui existe déjà. Le retrait n'est donc complet qu'une fois le bloc
`resource` supprimé du code, **et avec lui toutes les expressions qui
référencent encore ses attributs** ailleurs dans la configuration. Une seule
référence oubliée suffit à faire échouer le plan.

L'ordre compte : on retire du state, **puis** on nettoie le code. Dans l'autre
sens, la configuration décrit un objet de moins que le state, et Terraform
planifie une destruction.

## Le bloc `removed` : le même retrait, mais versionné

Le bloc déclare l'intention dans le code, où elle est relue, revue et rejouée à
l'identique par toute l'équipe. L'adresse s'écrit comme une référence, sans
guillemets :

```hcl
removed {
  from = random_pet.demo

  lifecycle {
    destroy = false
  }
}
```

Une condition est impérative : le bloc `resource` correspondant doit avoir
**disparu** de la configuration. Les deux ne coexistent pas, et Terraform refuse
de planifier tant que c'est le cas :

```text
Error: Removed resource still exists

  on main.tf line 20:
  20: resource "random_pet" "demo" {

This statement declares that random_pet.demo was removed, but it is still
declared in configuration.
```

Le bloc `resource` retiré, le plan annonce un retrait sans destruction. Notez le
marqueur en début de ligne, un point, distinct du `-` d'une suppression :

```text
 # random_pet.demo will no longer be managed by Terraform, but will not be destroyed
 # (destroy = false is set in the configuration)
 . resource "random_pet" "demo" {
        id        = "intent-stallion"
        # (2 unchanged attributes hidden)
    }

Plan: 0 to add, 0 to change, 0 to destroy.

Warning: Some objects will no longer be managed by Terraform

If you apply this plan, Terraform will discard its tracking information for
the following objects, but it will not delete them:
 - random_pet.demo
```

L'`apply` confirme que rien n'a bougé côté infrastructure :
`Apply complete! Resources: 0 added, 0 changed, 0 destroyed.` L'objet a quitté
le state, il n'a pas quitté l'existence.

## Le défaut du bloc `removed` est de détruire

Voici le point qui coûte cher, et que la syntaxe ne signale pas. Retirez le bloc
`lifecycle`, gardez le reste :

```hcl
removed {
  from = local_file.lot
}
```

Terraform accepte, **sans le moindre avertissement**, et planifie l'inverse de
ce que le mot « removed » laisse imaginer :

```text
  # local_file.lot[2] will be destroyed
  # (because local_file.lot is not in configuration)
  - resource "local_file" "lot" {
      - filename             = "./lot-2.txt" -> null
      - id                   = "f62fb50f2c6a58ed24da0bd2901ea4151b9a1890" -> null
    }

Plan: 0 to add, 0 to change, 3 to destroy.
```

À l'`apply`, les trois fichiers disparaissent du disque : `Apply complete!
Resources: 0 added, 0 changed, 3 destroyed.` La destruction est le comportement
**par défaut** du bloc, et `destroy = false` est ce qui l'en dispense. Trois
écritures, deux résultats :

| Écriture | Action planifiée | L'objet réel |
| --- | --- | --- |
| `removed` sans bloc `lifecycle` | `delete` | **détruit** |
| `removed` avec `lifecycle { destroy = true }` | `delete` | **détruit** |
| `removed` avec `lifecycle { destroy = false }` | `forget` | conservé |

## La preuve machine : `forget` contre `delete`

La sortie humaine se lit mal en revue et ne s'automatise pas. Le plan enregistré
puis converti en JSON tranche en un mot :

```bash
terraform plan -out=oubli.tfplan
terraform show -json oubli.tfplan
```

```json
[
  { "address": "local_file.lot[0]", "actions": ["create"] },
  { "address": "random_pet.demo",   "actions": ["forget"] }
]
```

L'action `forget` est celle d'un retrait sans destruction, un `delete` au même
endroit signe une suppression. C'est le contrôle à poser en revue ou en CI avant
tout `apply` qui porte un bloc `removed`, d'autant que la page officielle du
format JSON ne liste pas encore `forget` parmi les actions possibles : la valeur
se constate à l'exécution.

## Ce que `from` accepte, et ce qu'il refuse

Les deux mécanismes n'ont pas la même granularité. Une clé d'instance, que
`terraform state rm` traite sans broncher, est refusée par le bloc :

```text
Error: Resource instance keys not allowed

  on oubli.tf line 2, in removed:
   2:   from = local_file.lot[1]

Resource address must be a resource (e.g. "test_instance.foo"), not a
resource instance (e.g. "test_instance.foo[1]").
```

Un bloc `removed` porte donc sur la ressource **entière**, toutes instances
comprises. En revanche il accepte un **module entier**, ce qui n'a pas
d'équivalent plus simple :

```hcl
removed {
  from = module.stock

  lifecycle {
    destroy = false
  }
}
```

Le plan rend alors un `forget` par ressource contenue dans le module, ici
`module.stock.random_pet.interne`.

## Laquelle des deux, et quand

| Situation | Méthode |
| --- | --- |
| Retrait ponctuel, une instance précise (`[1]`, `["web"]`) | `terraform state rm` |
| Retrait qui doit être revu, tracé, rejoué par l'équipe | bloc `removed` |
| Migration d'un module vers un autre dépôt | bloc `removed` sur le module |
| Terraform antérieur à 1.7 | `terraform state rm`, seule option |

HashiCorp recommande les blocs `removed` et `import` pour **toute nouvelle
migration** : une commande impérative ne laisse aucune trace dans le dépôt, là
où un bloc versionné se relit et se rejoue. Une fois le retrait appliqué, garder
le bloc est sans conséquence, le plan suivant rend `No changes` : le supprimer
est une option de ménage, pas une obligation.

## À vous de jouer

Vous savez qu'un retrait du state ne détruit rien, qu'une ressource retirée mais
toujours déclarée devient une orpheline que le plan veut recréer, que le bloc
`removed` exige la disparition préalable du bloc `resource`, que son défaut est
de **détruire** et que `destroy = false` produit un `forget`. Le challenge vous
remet un projet à quatre ressources, dont deux doivent cesser d'être gérées sans
que leurs fichiers disparaissent, une par chaque voie.

```bash
dsoxlab run state-terraform-state-rm
dsoxlab check state-terraform-state-rm
dsoxlab hint state-terraform-state-rm
```

Sous-objectif d'examen visé : **1e** (inspecter et manipuler le state), niveau
Associate.

Référence : [terraform state rm](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-rm/)
