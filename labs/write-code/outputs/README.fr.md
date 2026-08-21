# Les outputs : type, sensibilité et precondition

Un **output** expose une valeur hors du module : le résultat d'une configuration,
lu par un humain, un autre module ou un pipeline. Le déclarer est simple. Ce qui
piège, c'est ce que `sensitive` **ne** masque **pas**, la façon dont la
sensibilité **se propage**, et le fait qu'un output n'est pas si passif : un
`precondition` peut faire échouer le plan. Ce tutoriel les montre sur un exemple
**jetable** de session ; le challenge vous les fera poser sur un autre cas.

## Un output expose une valeur

Sa syntaxe minimale est `value = <expression>`. Le bloc accepte aussi
`description`, `type` (contrainte de type, Terraform 1.15), `sensitive`,
`depends_on`, `precondition` et `ephemeral`.

```hcl
output "adresse" {
  value       = "https://${random_pet.session.id}.exemple.test"
  description = "URL publique de la session."
}
```

Depuis Terraform 1.15, on peut **contraindre son type**, exactement comme une
variable. C'est le contrat du module, et il documente ce que l'appelant recevra :

```hcl
output "profil" {
  type = object({
    nom    = string
    actif  = bool
  })
  value = {
    nom   = "session"
    actif = true
  }
}
```

## sensitive : un masque d'affichage, pas une protection

Voici le malentendu central. **`sensitive = true` ne protège pas le secret.** Il
masque la valeur dans la sortie **humaine** de `plan`, `apply` et
`terraform output`, et rien de plus. La documentation le dit :

> When you run Terraform commands with a local state file, Terraform stores the
> state as plain text, including variable values, even if you have flagged them
> as sensitive.

Concrètement, `terraform output -json`, `terraform output -raw` et le fichier
d'état rendent la valeur **en clair**. `-raw` ne fonctionne d'ailleurs que sur
une chaîne, un nombre ou un booléen, jamais sur une liste ou un objet.

```hcl
output "cle" {
  value     = random_password.session.result
  sensitive = true
}
```

## La sensibilité se propage, même à travers une fonction

C'est le piège que peu voient venir. **Toute expression qui utilise une valeur
sensible devient sensible.** Un output qui référence un attribut sensible **sans**
`sensitive = true` est **refusé au plan** :

```text
Error: Output refers to sensitive values
```

Et la contagion traverse les fonctions : le `sha256` d'un mot de passe **reste
sensible**, alors qu'un hachage n'est pourtant pas réversible. Pour exposer
sciemment une telle valeur dérivée, on la **déclassifie** avec `nonsensitive()` :

```hcl
output "empreinte" {
  value = nonsensitive(sha256(random_password.session.result))
}
```

<Aside type="caution" title="nonsensitive() est un engagement">
`nonsensitive()` retire la marque sensible : ne l'employez que sur une valeur
dont vous avez **prouvé** qu'elle ne divulgue rien, comme un hachage. L'appliquer
au secret lui-même l'exposerait en clair partout.
</Aside>

Pour exclure **réellement** une valeur du state et du plan, c'est `ephemeral =
true` (réservé aux **modules enfants**, interdit au module racine), pas
`sensitive`.

## Un output n'est pas passif : precondition et depends_on

On présente souvent l'output comme purement passif. C'est faux sur deux points.
Un bloc **`precondition`** (avec un `error_message` obligatoire) fait **échouer
le plan** si sa condition est fausse : c'est la garantie de dernière ligne d'un
module.

```hcl
output "adresse" {
  value = "https://${random_pet.session.id}.exemple.test"

  precondition {
    condition     = var.duree >= 10
    error_message = "duree doit valoir au moins 10."
  }
}
```

Et **`depends_on`** sur un output ordonne les opérations : Terraform termine les
ressources amont avant de calculer l'output, utile quand la dépendance n'apparaît
pas dans l'expression `value`.

## À vous de jouer

Vous savez qu'un output peut être **typé**, que `sensitive` ne masque que
l'affichage (le state garde le clair), que la sensibilité **se propage** même à
travers un `sha256` et se lève par `nonsensitive()`, et qu'un `precondition`
bloque le plan. Le challenge vous fait exposer un mot de passe et son empreinte
sans jamais fuiter le secret, et les tests le prouvent dans le JSON.

```bash
dsoxlab run write-code-outputs
dsoxlab check write-code-outputs
dsoxlab hint write-code-outputs
```

Sous-objectifs d'examen visés : **2f** (données sensibles) et **2e** (outputs et
types complexes).

Référence : [Les outputs en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/outputs-terraform/)
