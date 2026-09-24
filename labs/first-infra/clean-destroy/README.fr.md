# Détruire proprement, et les quatre choses que cela recouvre

« Détruire » désigne quatre opérations qui ne se ressemblent pas. Les confondre
mène à deux erreurs symétriques : croire qu'un garde-fou protège alors qu'il ne
protège plus, et supprimer un fichier qu'il fallait garder.

Le lab se joue **hors ligne**, sur les providers `random`, `local` et `null` :
tout est déterministe et rejouable.

## Les quatre gestes

| Geste | Ce qu'il fait |
| --- | --- |
| `destroy` global | tout, sauf ce qu'un garde-fou **refuse** |
| `destroy -target` | **uniquement** ce qu'on nomme |
| retirer du code | détruit au prochain `apply`, **sans aucun `destroy`** |
| `destroy` complet | vide le state, **sans supprimer son fichier** |

Le troisième est celui qu'on subit sans l'avoir demandé. Supprimer un bloc de
ressource n'est pas neutre : au prochain `apply`, Terraform constate que l'objet
existe et n'est plus déclaré, et il le détruit. C'est le mécanisme normal, et
c'est aussi la façon dont on perd une ressource en nettoyant un fichier.

## `prevent_destroy` refuse de planifier

```hcl
resource "local_file" "inventaire" {
  # ...
  lifecycle {
    prevent_destroy = true
  }
}
```

Ce n'est pas un verrou sur l'objet, c'est un **refus de planifier**. Il porte sur
tout plan qui emporterait la ressource, y compris un `destroy` global lancé sans
y penser.

Deux limites à connaître, et la seconde surprend :

- il ne protège plus rien dès que le **bloc quitte la configuration**. Le
  garde-fou est dans le code ; retirer le code retire le garde-fou ;
- **un plan qui échoue écrit quand même son fichier.** Mesuré en écrivant le
  lab : `terraform plan -destroy` sur une configuration protégée sort en **code
  1** et produit **quand même** le fichier demandé par `-out`. Ce plan est
  **incomplet**, trois ressources sur quatre, la ressource protégée entraînant
  ses dépendances hors du plan.

Un fichier de plan qui existe alors que la commande a échoué est exactement le
genre de chose dont personne ne se méfie. On le relit, on le croit, et il ment
par omission.

## Un plan de destruction se lit avant de s'exécuter

```bash
terraform plan -destroy -out=destroy.tfplan
terraform show -json destroy.tfplan | jq '[.resource_changes[].address]'
```

C'est la seule façon de savoir ce qu'un `destroy` va emporter **avant** qu'il
l'emporte. Sur une configuration réelle, la liste réserve souvent des surprises :
des ressources créées par un module, ou dépendantes de celle qu'on visait.

## Le state se vide, son fichier reste

C'est le piège de fin de lab, et il coûte cher hors du lab :

```console
$ terraform destroy -auto-approve
$ terraform show -json | jq '.values.root_module.resources'
null
$ ls terraform.tfstate
terraform.tfstate
```

Le fichier est toujours là, et il **doit** l'être. Il porte le `lineage` du
projet et son `serial`. Le supprimer « pour faire propre » fait repartir
Terraform de zéro : il perd le lien avec tout ce qui aurait survécu, et il ne
sait plus qu'il a déjà géré ces objets.

Vider le state et supprimer son fichier sont deux choses différentes. Le lab
vérifie les deux séparément, et c'est volontaire.

## À vous de jouer

```bash
dsoxlab run first-infra-clean-destroy
dsoxlab check first-infra-clean-destroy
dsoxlab hint first-infra-clean-destroy
```

Cinq tests. Le garde-fou est jugé sur le **code de retour** et non sur le
message, parce qu'un texte change avec les versions. Le plan de destruction est
jugé sur le **nombre d'adresses**, parce qu'un test qui vérifierait la seule
existence du fichier passerait sur un plan mutilé.

Sous-objectif d'examen visé : **1d**, avec appui sur **1e**.

Référence : [détruire proprement](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/destroy-propre/)
