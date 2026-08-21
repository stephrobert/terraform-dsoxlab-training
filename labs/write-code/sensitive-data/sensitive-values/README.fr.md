# sensitive : un masque, et un effet de bord

`sensitive = true` masque une valeur dans l'affichage, mais **ne la retire pas du
state**. Et le marquage a un **effet de bord** qu'on ne soupçonne pas : la
sensibilité se propage, et elle **interdit** certaines constructions comme
`for_each`. Ce tutoriel le montre sur un exemple **jetable** ; le challenge vous
fait éviter le piège et exposer un hash sans fuiter.

## sensitive masque l'affichage, pas le state

```hcl
variable "cle_api" {
  type      = string
  sensitive = true
}
```

`terraform output -json` et `terraform output -raw` rendent la valeur **en
clair**, et le state la conserve. `sensitive` est un filtre d'affichage.

## L'effet de bord : sensitive casse for_each

Voici le piège Professional. **Une valeur sensible ne peut pas servir de clé
`for_each`** :

```hcl
variable "zones" {
  type      = set(string)
  sensitive = true
}

resource "local_file" "f" {
  for_each = var.zones # interdit
}
```

```text
Error: Invalid for_each argument
```

Terraform utilise la valeur de `for_each` comme **identifiant d'instance** et
l'affiche toujours, ce qui divulguerait le secret. Marquer une variable
`sensitive` peut donc **casser** un `for_each` qui marchait. La parade : itérer
sur un ensemble **non sensible**, et n'injecter le secret que dans un attribut.

## La contamination est tracée dans sensitive_values

Un attribut alimenté par une valeur sensible devient sensible, et `show -json` le
signale dans un objet **`sensitive_values`** par ressource :

```bash
terraform show -json | jq '.values.root_module.resources[] | {address, sensitive_values}'
```

C'est la trace machine pour auditer ce que la propagation a réellement contaminé.

## Exposer un hash sans fuiter : nonsensitive()

Le `sha256` d'un secret **reste sensible** (la contagion traverse les fonctions).
Pour publier une empreinte sûre dans un output non sensible, on la déclassifie :

```hcl
output "hash_cle" {
  value = nonsensitive(sha256(var.cle_api))
}
```

`nonsensitive()` engage votre responsabilité : à réserver à une valeur qui ne
divulgue rien, comme un hachage.

## À vous de jouer

Vous savez qu'une valeur sensible **ne peut pas** être une clé `for_each`, que la
contamination se lit dans `sensitive_values`, et que `nonsensitive()` déclassifie
un hash. Le challenge vous fait itérer sur des clés non sensibles tout en
injectant un secret, et exposer son empreinte, et les tests le prouvent dans le
JSON.

```bash
dsoxlab run write-code-sensitive-data-sensitive-values
dsoxlab check write-code-sensitive-data-sensitive-values
dsoxlab hint write-code-sensitive-data-sensitive-values
```

Sous-objectif d'examen visé : **2f** (données sensibles).

Référence : [sensitive en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/sensitive-terraform/)
