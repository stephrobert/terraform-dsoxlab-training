# Structurer un projet Terraform : ce qui compte, et ce qui ne compte pas

`main.tf`, `variables.tf`, `outputs.tf` : la convention est partout, et elle est
utile. Mais il faut savoir ce qu'elle est exactement, parce que beaucoup de
débutants croient qu'elle a un effet sur l'exécution. **Elle n'en a aucun.**

## Terraform lit un répertoire, pas des fichiers

Terraform charge **tous** les `.tf` d'un répertoire et les évalue comme un seul
document. Le nom des fichiers, leur nombre, leur ordre : rien de tout cela n'a
d'effet fonctionnel.

Deux conséquences, opposées et également importantes.

**La bonne** : vous pouvez réorganiser librement. Déplacer un bloc d'un fichier
à l'autre ne change strictement rien au plan. C'est un refactoring sans risque,
et c'est démontrable.

**La mauvaise** : un fichier oublié compte quand même. Renommez `tout.tf` en
`tout.tf.old` et Terraform l'ignore, car l'extension n'est plus `.tf`. Mais
laissez-le en `.tf` à côté de votre nouveau découpage, et **chaque bloc est
déclaré deux fois**.

```text
Error: Duplicate variable declaration

  A variable named "projet" was already declared at variables.tf:1,1-19.
```

## La convention, et pourquoi elle tient

| Fichier | Ce qu'il porte |
|---|---|
| `terraform.tf` | le bloc `terraform` : `required_version`, `required_providers` |
| `providers.tf` | les blocs `provider`, leurs alias, leurs régions |
| `variables.tf` | les blocs `variable` |
| `locals.tf` | le ou les blocs `locals` |
| `main.tf` | les `resource` et les `data` |
| `outputs.tf` | les blocs `output` |

Elle tient parce qu'elle répond à une question de lecture : « où est déclaré
`projet` ? » se répond sans `grep`. Sur un module de quinze lignes, elle est
inutile ; sur un projet réel, elle est ce qui permet à quelqu'un d'autre
d'entrer dedans.

## Prouver qu'un découpage n'a rien changé

C'est la partie qu'on saute d'habitude, et c'est la seule qui compte :

```bash
terraform plan -out=reference.tfplan
terraform show -json reference.tfplan > plan-reference.json
# ... découpage ...
terraform plan -out=apres.tfplan
terraform show -json apres.tfplan > plan-apres.json
```

Puis on compare les deux `resource_changes`, adresse par adresse. Une seule
divergence, et un bloc a été perdu ou retouché pendant le déplacement.

<Aside type="caution" title="Ne comparez pas les fichiers JSON tels quels">
Un plan porte un `timestamp` et une `terraform_version` qui changent d'un appel
à l'autre sans que la configuration bouge. Comparez les `resource_changes`, pas
les documents entiers.
</Aside>

## La précédence des valeurs, dans l'ordre réel

Quand plusieurs sources donnent une valeur à la même variable, Terraform les
applique dans un ordre fixe, **du plus faible au plus fort** :

1. le `default` du bloc `variable` ;
2. la variable d'environnement **`TF_VAR_<nom>`** ;
3. le fichier **`terraform.tfvars`** ;
4. le fichier **`terraform.tfvars.json`** ;
5. les fichiers **`*.auto.tfvars`**, chargés en **ordre alphabétique** ;
6. les options **`-var`** et **`-var-file`** de la ligne de commande.

Le rang de `TF_VAR_` est celui qu'on place presque toujours trop haut. Une
variable d'environnement **ne l'emporte pas** sur un `terraform.tfvars` : elle
est juste au-dessus du `default`, et en dessous de tout fichier de valeurs.

```bash
export TF_VAR_projet=depuis-l-environnement
# avec projet = "catalogue" dans terraform.tfvars
terraform apply
terraform output projet_effectif     # "catalogue"
```

Entre deux `*.auto.tfvars`, c'est l'ordre **alphabétique** qui tranche, pas
l'ordre d'écriture ni la date de modification. Et la ligne de commande gagne
toujours.

## À vous de jouer

Vous savez maintenant que le nom des fichiers n'a aucun effet fonctionnel, que
laisser le monolithe en place redéclare tout en double, qu'un découpage se
prouve en comparant deux plans, et que `TF_VAR_` est plus faible qu'un fichier
de valeurs.

Le challenge vous fait découper un monolithe, puis produire ces preuves.

```bash
dsoxlab run getting-started-terraform-project-structure
dsoxlab check getting-started-terraform-project-structure
dsoxlab hint getting-started-terraform-project-structure
```

Sous-objectif d'examen visé : **2e** (déclarer et consommer variables et
outputs, y compris la précédence des valeurs), avec **2a** en appui.

Référence : [Structurer un projet Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/structure-projet-terraform/)
