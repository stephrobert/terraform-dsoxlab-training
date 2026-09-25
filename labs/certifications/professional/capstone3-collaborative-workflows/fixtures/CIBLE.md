# Ce qu'il faut obtenir

Deux configurations séparées, un state partagé, et **aucune interaction
humaine**.

## Le contrat entre les deux stacks

`reseau/` **publie**, `application/` **consomme**. Aucune expression ne traverse
la frontière entre deux configurations : la seule passerelle est la lecture de
l'**état distant**, par ses outputs déclarés.

## Les quatre exigences

1. **Les versions sont contraintes.** `required_version` sur le binaire, et une
   contrainte sur chaque provider. Une configuration collaborative qui laisse
   flotter ses versions ne se comporte pas pareil chez deux personnes.

2. **Les deux states vivent dans le bucket S3**, sous deux clés distinctes.
   Plus aucun `terraform.tfstate` local.

3. **`application/` lit les valeurs de `reseau/`** par `terraform_remote_state`.
   Aucune valeur recopiée : changer une valeur en amont doit se propager.

4. **Tout s'exécute en automation** : `-input=false`, et le cycle en deux temps
   que fait une CI, `plan -out` puis `apply` du **fichier de plan**.

## Pourquoi le plan en deux temps

Un `apply` direct relit la configuration au moment d'appliquer. Ce qui a été
revu n'est donc pas forcément ce qui sera appliqué.

Appliquer un plan **enregistré** ferme cet écart : ce qui a été relu en revue
est exactement ce qui part en production, et l'apply n'attend aucune
confirmation.
