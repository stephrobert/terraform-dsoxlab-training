# Contraindre la version de la CLI et verrouiller les providers

Installer le binaire ne prouve presque rien. Ce qui compte, c'est qu'une même
configuration se comporte **de la même façon sur tous les postes de l'équipe**,
et cela repose sur deux mécanismes distincts que l'on confond souvent.

## Deux contraintes, deux objets

```hcl
terraform {
  required_version = ">= 1.11.0, < 2.0.0"   # la CLI

  required_providers {                       # les providers
    local  = { source = "hashicorp/local",  version = "~> 2.5" }
    null   = { source = "hashicorp/null",   version = "~> 3.2" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}
```

`required_version` ne porte **que** sur la version de la CLI, jamais sur celle
des providers. C'est explicite dans la documentation, et c'est la première chose
à retenir : épingler Terraform n'épingle rien de ce qu'il télécharge.

Il faut aussi distinguer cette contrainte de celle que pose l'outillage. Un
`mise.toml` ou un `.terraform-version` dit **quelle CLI installer** sur votre
poste. `required_version` dit **quelle CLI a le droit d'exécuter cette
configuration**, et il voyage avec elle. Le premier est une préférence locale,
le second un contrat du dépôt.

## Le refus est net, et c'est le but

Une contrainte insatisfiable ne produit pas un avertissement : elle **empêche
l'exécution**.

```console
$ terraform init
│ Error: Unsupported Terraform Core version
$ echo $?
1
```

C'est exactement ce qu'on veut : mieux vaut un refus immédiat qu'un apply mené
par une version qui interprète autrement ce qu'elle lit. Le lab fait provoquer ce
refus dans un sous-répertoire dédié, parce qu'un mécanisme de sécurité qu'on n'a
jamais vu se déclencher n'est pas un mécanisme connu.

## Le verrou fait autorité, et il est fait pour être commité

`terraform init` produit `.terraform.lock.hcl`. Ce n'est pas un cache : c'est un
fichier **machine, à versionner**, qui fige les versions résolues et leurs
sommes de contrôle.

```hcl
provider "registry.terraform.io/hashicorp/local" {
  version     = "2.9.1"
  constraints = "~> 2.5"
  hashes = [
    "h1:...",
  ]
}
```

La preuve qu'il fait autorité tient en trois commandes, et c'est celle que le lab
exige :

```bash
terraform version -json | jq .provider_selections   # relever
rm -rf .terraform/
terraform init
terraform version -json | jq .provider_selections   # strictement identique
```

Supprimer `.terraform/` ne fait pas glisser les versions vers les plus récentes.
Si elles bougeaient, le verrou ne servirait à rien.

## Un verrou d'une seule plateforme casse chez le collègue

C'est le piège le plus coûteux du lot, parce qu'il ne se voit qu'ailleurs. Les
sommes de contrôle sont **par plateforme**. Un verrou créé sur Linux ne contient
pas les sommes pour macOS : le collègue qui l'utilise verra son `init` échouer
sur un fichier que vous avez pourtant commité.

```bash
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_arm64
```

Cette commande est à relancer **à chaque fois qu'une contrainte change**, et
c'est ce que le lab vérifie : au moins deux plateformes dans le verrou.

## À vous de jouer

```bash
dsoxlab run getting-started-install-terraform
dsoxlab check getting-started-install-terraform
dsoxlab hint getting-started-install-terraform
```

Le lab est de type `shell` : aucune VM, aucun cloud, et le réseau n'est
nécessaire que pour télécharger les providers.

Les cinq preuves échouent toutes si vous vous êtes contenté d'installer le
binaire : c'est délibéré.

Sous-objectif d'examen visé : **3a**.

Référence : [installer Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/installer-terraform/)
