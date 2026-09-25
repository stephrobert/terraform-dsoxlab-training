# Un mot, deux sens : le workspace CLI et celui de HCP Terraform

L'objectif 6 du Professional est le seul évalué **en QCM** : HashiCorp ne demande
aucune manipulation dans HCP Terraform. Ce lab ne réclame donc **aucun compte et
aucun `terraform login`**, et il prouve pourtant quelque chose de réel, parce
qu'un bloc `cloud` est contrôlé bien avant toute authentification.

Ce qu'il traite est une confusion dont l'examen se sert : le même mot désigne
deux choses très différentes.

## Un workspace CLI est un state, et rien d'autre

```bash
terraform workspace new staging
```

Cela crée **un état de plus** dans le même répertoire, à partir de la même
configuration. Pas de variables propres, pas de droits, pas d'historique, pas
d'exécution. C'est une façon de tenir plusieurs instances d'une infrastructure,
et cela s'arrête là.

## Un workspace HCP Terraform est une unité d'exécution

Il porte ses **variables d'entrée**, ses **droits**, son **historique de runs**
et son state. Deux workspaces d'une même organisation peuvent exécuter deux
configurations entièrement différentes.

D'où la conséquence que les candidats manquent : avec HCP Terraform, les
variables d'entrée d'un run vivent **dans le workspace**, pas dans un fichier du
dépôt.

| | Workspace CLI | Workspace HCP Terraform |
| --- | --- | --- |
| Ce qu'il porte | un state | un state, des variables, des droits, un historique |
| Où il vit | dans le backend, à côté des autres | dans une organisation |
| Ses variables | celles du répertoire | les siennes |
| Ses droits | ceux de la machine | des équipes, par workspace |

## Deux stratégies de rattachement, et elles s'excluent

Un répertoire se rattache à HCP Terraform par le bloc `cloud`, et il le fait de
l'une de ces deux façons :

```hcl
cloud {
  organization = "atelier-dsoxlab"

  workspaces {
    name = "app-prod"          # un workspace désigné
  }
}
```

```hcl
cloud {
  organization = "atelier-dsoxlab"

  workspaces {
    project = "plateforme"     # restreint la sélection à un projet
    tags    = { env = "prod" } # tous les workspaces correspondants
  }
}
```

`name` et `tags` ne peuvent pas figurer ensemble : l'un désigne un workspace
unique, l'autre en sélectionne un ensemble. Terraform répond `Invalid workspaces
configuration`.

Mesuré le 2026-09-25 sur Terraform 1.16.1 : `tags` est accepté **aussi bien**
sous forme de liste de mots que de map clé-valeur, et `project` seul ne suffit
pas. Un bloc `workspaces` qui ne porte qu'un `project`, ou qui ne porte rien,
échoue sur un message qui ne nomme ni l'un ni l'autre :

```
Error: failed to create backend alias to target "".
The hostname is not in the correct format.
```

## Où un bloc `cloud` est contrôlé, et pourquoi `validate` ne le voit pas

C'est la vraie leçon du lab, et elle se mesure au lieu de se raconter.

Un bloc `cloud` est résolu **avant** toute évaluation d'expression, au moment où
Terraform établit où vit le state. Il ne peut donc référencer aucune valeur
nommée, pas même une variable avec une valeur par défaut :

```hcl
cloud {
  organization = var.organisation   # Error: Variables not allowed
}
```

Ce qui conduit à un résultat qui vaut d'être retenu. Sur trois fautes posées dans
le même fichier :

| Faute | `terraform validate` | `terraform init` |
| --- | --- | --- |
| un bloc `backend` à côté de `cloud` | **l'attrape** | l'attrape |
| `organization = var.x` | `Success!` | `Variables not allowed` |
| `name` et `tags` ensemble | `Success!` | `Invalid workspaces configuration` |

`terraform validate` répond « Success! The configuration is valid. » sur deux
fautes qui font échouer l'`init`. Il contrôle la syntaxe de la configuration et
sa cohérence interne, pas le rattachement. Un `validate` vert ne dit donc rien de
la justesse de votre bloc `cloud`.

## La frontière d'un lab sans compte

Un bloc `cloud` correct va jusqu'à l'authentification et s'y arrête :

```
Initializing HCP Terraform...

Error: Required token could not be found
```

C'est ce qui rend le lab vérifiable sans compte : une configuration fautive
n'atteint jamais ce point. Mais ce message seul ne prouve rien, et la mesure dit
pourquoi : une configuration portant à la fois un `backend` et un `cloud`
l'affiche **aussi**, juste à côté de sa faute. Les tests exigent donc les deux,
le message de jeton présent et aucun message de faute.

## À vous

```bash
dsoxlab run hcp-terraform-hcp-workspaces
dsoxlab check hcp-terraform-hcp-workspaces
dsoxlab hint hcp-terraform-hcp-workspaces
```

Huit tests. Deux répertoires à réparer, cinq réponses à établir, et aucun compte
à créer : les tests neutralisent tout jeton présent sur le poste, pour que la
mesure soit la même partout.

Sous-objectif d'examen visé : **6b**.

Référence : [se connecter à HCP Terraform](https://developer.hashicorp.com/terraform/cli/cloud/settings)
