# Deux configurations d'un même provider, et une erreur à diagnostiquer

Le cinquième objectif du Professional porte sur les providers : leur
architecture, leur configuration, leur authentification, et le diagnostic de
leurs erreurs. Ce capstone les fait tenir ensemble.

Le lab se joue sur **Floci**, un émulateur AWS local : aucun compte, aucune
facture.

## Un provider, plusieurs configurations

Un provider est un **plugin**. Terraform en télécharge le binaire, puis lui
passe une configuration. Rien n'empêche de lui en passer **plusieurs** :

```hcl
provider "aws" {
  region = "eu-west-3"
}

provider "aws" {
  alias  = "archives"
  region = "us-east-1"
}
```

`alias` est le seul argument qui distingue la seconde de la première, et sans
lui Terraform refuse le doublon. C'est aussi lui qui permet de la **désigner** :

```hcl
resource "aws_instance" "archives" {
  provider = aws.archives
}
```

Point qui surprend : **rien ne s'hérite** d'une configuration à l'autre. Chacune
porte ses options, ses identifiants, son endpoint. C'est ce qui permet d'avoir
deux régions, deux comptes ou deux jeux d'identifiants dans une seule
configuration.

## L'oubli qui ne se voit pas

Sans l'argument `provider`, une ressource utilise la configuration **par
défaut**. Elle est donc créée au mauvais endroit, et **rien ne le signale** :
deux instances EC2 se ressemblent, l'état ne dit pas quelle configuration les a
produites.

Le seul endroit qui le dit est la section `configuration` du plan JSON :

```console
$ terraform show -json plan.tfplan | jq '.configuration.root_module.resources[]
    | {address, provider_config_key}'
{"address":"aws_instance.principal","provider_config_key":"aws"}
{"address":"aws_instance.archives","provider_config_key":"aws.archives"}
```

## L'erreur d'authentification, et ce qu'elle dit vraiment

La configuration de départ échoue, et le message nomme ce qu'il n'a pas trouvé :

```text
Error: No valid credential sources found
failed to refresh cached credentials, no EC2 IMDS role found
```

Le provider cherche des identifiants **dans l'ordre** : l'environnement, puis
`~/.aws`, puis la métadonnée d'instance EC2. Cette dernière n'existe pas hors
d'une instance, d'où le message final.

Trois options le dispensent de ces recherches, et elles ne servent pas à la même
chose :

| Option | Ce qu'elle évite |
| --- | --- |
| `skip_credentials_validation` | valider l'identité auprès de STS |
| `skip_requesting_account_id` | demander à quel compte on appartient |
| `skip_metadata_api_check` | interroger la métadonnée d'instance |

Plus des identifiants factices **non vides**, que l'émulateur accepte sans les
vérifier.

## Une preuve qui sort de Terraform

Mesure faite en écrivant le lab : **Floci isole par région**. Une instance créée
en `us-east-1` est invisible depuis une requête `eu-west-3`.

Le lab s'en sert : chaque instance doit être vue dans **sa** région et **absente
de l'autre**. C'est ce qui prouve, hors de tout ce que Terraform raconte, que
deux configurations différentes les ont produites. Une ressource qui aurait pris
la configuration par défaut se verrait des deux côtés au même endroit.

## Un environnement sans identifiants

Les tests lancent Terraform sans aucune variable `AWS_*` et avec un `HOME` sans
`.aws`. Sans cette précaution, le lab passerait chez qui a des credentials
configurés et échouerait chez les autres : il mesurerait le poste, pas le
travail.

## À vous de jouer

```bash
dsoxlab run certifications-professional-capstone5-providers
dsoxlab check certifications-professional-capstone5-providers
dsoxlab hint certifications-professional-capstone5-providers
```

Six tests. Le dernier détruit les deux instances quoi qu'il arrive : chacune est
un vrai conteneur chez Floci, avec un port retenu.

Objectif d'examen visé : **5**, dans ses quatre sous-objectifs.

Référence : [le programme du Terraform Authoring and Operations Professional](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
