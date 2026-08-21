# Découper une configuration ne se prouve pas avec `validate`

Découper un `main.tf` devenu illisible est le premier réflexe d'hygiène d'un
dépôt Terraform. C'est aussi l'opération dont on répète le plus souvent qu'elle
est **sans risque**, au motif que `terraform validate` passe ensuite. Cette
garantie n'existe pas.

## Ce que `validate` ne regarde pas

La documentation borne son périmètre sans ambiguïté : « The `validate` command
does not check if argument values are valid for a specific provider, but it will
verify that they are the **correct type**. It does not evaluate any existing
state. »

Traduit en pratique : un bloc **perdu** au copier-coller, une variable qui ne
vient plus du même fichier, une ressource dupliquée sous un autre nom passent
`validate` sans un mot. Mesuré, sur un découpage où une ressource et sa sortie ont
disparu :

```text
Success! The configuration is valid, but there were some validation warnings
```

La configuration est **valide**, et le plan n'a plus rien à voir. Le seul contrôle
qui prouve l'invariance est la **comparaison de deux plans**.

```bash
# avant le decoupage
terraform plan -out=avant.tfplan && terraform show -json avant.tfplan > avant.json

# apres
terraform plan -out=apres.tfplan && terraform show -json apres.tfplan > apres.json

diff <(jq -S '.planned_values, .resource_changes' avant.json) \
     <(jq -S '.planned_values, .resource_changes' apres.json)
```

La section `configuration` du JSON, elle, **change** légitimement : c'est la
représentation du code, qui reflète le découpage. Ce sont `planned_values`,
`resource_changes` et `output_changes` qui doivent rester **identiques**.

## Le socle de fichiers, et les noms qui surprennent

Le *style guide* officiel nomme les fichiers, et deux de ces noms ne sont pas
ceux qu'on lit partout :

| Fichier | Ce qu'il contient |
| --- | --- |
| `terraform.tf` | **un seul** bloc `terraform`, `required_version` et `required_providers` |
| `providers.tf` | **tous** les blocs `provider`, avec « always include a default provider configuration » |
| `variables.tf` | tous les `variable`, en **ordre alphabétique** |
| `outputs.tf` | tous les `output`, en **ordre alphabétique** |
| `main.tf` | les `resource` **et** les `data source` |

Le nom `versions.tf`, très répandu, n'apparaît **nulle part** dans la
documentation. Et le bloc `provider` a son fichier à lui, pas une place au chaud
à côté du bloc `terraform`.

<Aside>Rien de tout cela n'est imposé par Terraform : le moteur charge **tous**
les `.tf` d'un répertoire et les traite comme un seul document. C'est justement
pour cela qu'il vaut mieux suivre la convention **publiée** que la sienne.</Aside>

## L'exception qui contredit la règle

Une famille de noms **a** un effet fonctionnel : `override.tf`, `override.tf.json`
et tout fichier en `_override.tf`. Terraform les charge **en dernier** et
**fusionne** leur contenu par-dessus les blocs existants. Un fichier ainsi nommé
n'est donc pas un fichier comme les autres, et ce n'est pas non plus un fichier
« généré » : le style guide le range parmi les fichiers du module.

## Formater toute l'arborescence

`terraform fmt -check` ne regarde que le **répertoire courant**. Sur une
arborescence à plusieurs niveaux, c'est un contrôle qui rassure sans rien
vérifier.

```bash
terraform fmt -check -recursive
```

La documentation nomme l'option pour ce cas précis : « The `terraform fmt` command
can use the `-recursive` flag for subdirectories. » Sans elle, votre intégration
continue reste **verte** avec des sous-répertoires mal formatés.

## Le `.gitignore`, et le piège du plan enregistré

Trois familles ne se committent **jamais** : le répertoire `.terraform/`, l'état
et ses sauvegardes, et les **plans enregistrés**. Ce dernier point cache le piège :

```bash
terraform plan -out=tfplan
```

Ce fichier n'a **aucune extension**. Un `.gitignore` qui ne connaît que
`*.tfplan` ne l'attrape pas, et un plan enregistré contient les valeurs
**résolues**, secrets compris.

À l'inverse, un fichier doit **toujours** être versionné : `.terraform.lock.hcl`.
C'est lui qui garantit que toute l'équipe emploie les mêmes versions de providers.

Un `.gitignore` ne se vérifie pas en le **lisant**, mais en le faisant
**travailler** :

```bash
git check-ignore -v projet/tfplan projet/terraform.tfstate
git check-ignore projet/.terraform.lock.hcl && echo "PROBLEME : le verrou est ignore"
```

## À vous de jouer

Vous savez ce que `validate` ne couvre pas, comment prouver qu'un découpage n'a
rien changé, quels noms de fichiers la documentation retient, pourquoi `-recursive`
est indispensable, et ce qu'un `.gitignore` doit laisser passer. Le challenge vous
remet une configuration monolithique à découper, avec le plan comme juge.

```bash
dsoxlab run environments-organize-terraform-repo
dsoxlab check environments-organize-terraform-repo
dsoxlab hint environments-organize-terraform-repo
```

Il se joue **hors ligne**.

Sous-objectif d'examen visé : **2a** (écrire et organiser une configuration).

Référence : [organiser un dépôt Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/organiser-repo-terraform/)
