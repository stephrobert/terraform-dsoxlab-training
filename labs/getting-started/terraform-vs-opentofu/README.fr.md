# Terraform et OpenTofu : jusqu'où va la compatibilité

OpenTofu est un fork de Terraform, né du changement de licence de 2023. La
phrase qui revient partout est « les deux outils sont compatibles ». Elle est
vraie, et elle est incomplète. Ce tutoriel montre ce qui se transporte
réellement d'un binaire à l'autre, et l'endroit précis où ça cesse.

## Le sourcing implicite, ou le pari que personne ne voit

Écrivez une ressource `random_pet` sans rien déclarer. Terraform devine :
`hashicorp/random`, sur `registry.terraform.io`. OpenTofu devine aussi :
`hashicorp/random`, mais sur `registry.opentofu.org`.

Tant que les deux registres publient la même chose, personne ne remarque rien.
Le jour où ils divergent, votre configuration résout deux providers différents
selon le binaire qui la lit, et rien dans le code ne le disait.

```hcl
terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
```

**Déclarer, c'est retirer la devinette.** Le `source` nomme l'organisation, la
contrainte borne la version, et le fichier de verrouillage enregistre ce qui a
été retenu.

## La contrainte pessimiste

`~> 3.6` est la forme à connaître. Elle accepte `3.6.0`, `3.9.1`, et refuse
`4.0.0` : la composante majeure est verrouillée, les correctifs restent
accessibles.

| Forme | Effet |
|---|---|
| `= 3.6.0` | figée : aucun correctif, jamais |
| `>= 3.6` | flottante : `4.0` passera, et cassera |
| `~> 3.6` | pessimiste : `3.x` oui, `4.0` non |

Une version flottante est exactement ce que le sourcing implicite laisse
faire : chaque binaire résout ce qu'il veut.

## Ce qui se transporte : le state

C'est la bonne nouvelle, et elle est solide. Appliquez avec `terraform`, puis
lancez `tofu` sur le même répertoire :

```bash
terraform apply -auto-approve
tofu init
tofu plan -detailed-exitcode ; echo $?   # 0
tofu output nom_animal                   # la même valeur
```

**Aucune destruction, aucune recréation.** Le state est lu tel quel, les mêmes
versions de providers sont retenues, et le plan est vide. La compatibilité
annoncée existe bel et bien, à cet endroit.

## Ce qui ne se transporte pas : le verrou

Regardez maintenant `.terraform.lock.hcl` après le passage de `tofu` :

```text
provider "registry.opentofu.org/hashicorp/local" {
provider "registry.opentofu.org/hashicorp/null" {
provider "registry.opentofu.org/hashicorp/random" {
```

Les adresses `registry.terraform.io` ont **disparu**. Et `terraform` s'arrête
net :

```text
Error: Inconsistent dependency lock file

  - provider registry.terraform.io/hashicorp/local: required by this
    configuration but no version is selected
```

La réparation est simple, `terraform init -upgrade`, et le plan revient à `0` :
l'aller-retour n'a modifié ni le state ni l'infrastructure. Mais elle n'est pas
automatique, et dans une équipe où chacun choisit son binaire, le verrou
bascule à chaque commit.

<Aside type="caution" title="Le verrou n'enregistre ses contraintes qu'une fois">
`constraints` n'est inscrit dans `.terraform.lock.hcl` qu'à la **création** de
l'entrée. Si vous lancez `init` avant d'écrire vos contraintes, le verrou reste
sans elles, et rien ne les y ajoutera ensuite, pas même `init -upgrade`. Pour
repartir proprement, supprimez le fichier et relancez `init`.
</Aside>

## À vous de jouer

Vous savez maintenant que le sourcing implicite est un pari silencieux, qu'une
contrainte pessimiste borne la majeure sans interdire les correctifs, que le
state se transporte réellement d'un outil à l'autre, et que le fichier de
verrouillage est l'endroit exact où la compatibilité s'arrête.

Le challenge vous fait rendre une configuration portable, puis produire ces
preuves.

```bash
dsoxlab run getting-started-terraform-vs-opentofu
dsoxlab check getting-started-terraform-vs-opentofu
dsoxlab hint getting-started-terraform-vs-opentofu
```

Sous-objectif d'examen visé : **5b** (configuration des providers : sourcing et
versionnement), avec appui sur **3a**.

Référence : [Terraform ou OpenTofu](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/terraform-vs-opentofu/)
