# Première infrastructure : le cycle complet, prouvé

Quatre commandes, et le tutoriel est fini : `init`, `plan`, `apply`, `destroy`.
Ce lab existe parce que les dérouler n'est pas la même chose que les **prouver**,
et parce qu'une seule ligne de `versions.tf` décide du langage dans lequel vous
écrivez sans que rien ne vous le dise.

Il se joue sur **libvirt**, c'est-à-dire sur une vraie infrastructure locale, et
c'est la seule section du parcours où ce provider est autorisé. Aucune image
cloud à télécharger : un volume vierge suffit à prouver le cycle.

## `~> 0.8` n'interdit pas `0.9.x`

C'est le piège qui a motivé ce lab, et il vient d'un audit du guide. L'opérateur
pessimiste laisse flotter le composant le plus à **droite** de ce qui est écrit :

| Contrainte | Accepte | Refuse |
| --- | --- | --- |
| `~> 0.8` | `0.8.9`, **`0.9.9`** | `1.0.0` |
| `~> 0.9.0` | `0.9.9` | **`0.10.0`** |

Avec **deux** composants, c'est donc le **mineur** qui flotte. Écrire `~> 0.8`
en pensant « la série 0.8 » installe aujourd'hui la 0.9.9.

Ce serait sans conséquence si les versions se ressemblaient. Or la branche 0.9
de `dmacvicar/libvirt` a **réécrit le schéma** de presque toutes ses
ressources :

```hcl
# schéma 0.8
resource "libvirt_volume" "disque" {
  size   = 1073741824
  format = "qcow2"
}

# schéma 0.9
resource "libvirt_volume" "disque" {
  capacity      = 1
  capacity_unit = "GiB"
  target = {
    format = { type = "qcow2" }
  }
}
```

Laisser flotter le mineur, c'est laisser flotter le **langage**. Votre code
s'applique chez vous et casse chez le collègue dont le verrou a retenu l'autre
série, avec un message qui parle d'argument inattendu et jamais de version.

## Le verrou garde la contrainte du jour où il est né

Fait mesuré en écrivant le lab, et qui surprend : `.terraform.lock.hcl` écrit
son champ `constraints` à la **création** de l'entrée, et ne le met plus à jour
ensuite. Ni `init`, ni `init -upgrade` ne le corrigent.

```hcl
provider "registry.terraform.io/dmacvicar/libvirt" {
  version     = "0.9.9"
  constraints = "~> 0.8"   # la contrainte d'origine, pas celle du fichier actuel
}
```

Un verrou peut donc annoncer une contrainte que votre `versions.tf` ne porte
plus. C'est pourquoi le test du lab reconstruit le verrou dans une **copie**
plutôt que de lire celui qui traîne : il vérifie la contrainte **déclarée**, et
non la version résolue, qui vaudrait 0.9.9 dans les deux cas.

## La capacité n'est pas convertie pour vous

Autre mesure, et elle coûte un cycle à qui ne la connaît pas : le provider
**n'applique pas** `capacity_unit` à `capacity`. Déclarer `capacity = 1` avec
`capacity_unit = "GiB"` crée un volume d'**un octet**, arrondi au bloc.

Le lab compare donc la capacité **effective** lue dans l'état, pas les deux
attributs déclarés. C'est la différence entre vérifier ce qu'on a écrit et
vérifier ce qui existe.

## Sortir de Terraform pour vérifier Terraform

L'état est le **rapport** de Terraform sur le monde. Il dit ce que Terraform
croit. Pour prouver qu'un volume existe, il faut demander à quelqu'un d'autre :

```console
$ virsh -c qemu:///system vol-list default
 Nom                     Chemin
------------------------------------------------------------
 tf-lab-premiere.qcow2   /var/lib/libvirt/images/tf-lab-premiere.qcow2
```

Le lab croise les deux : le chemin annoncé par l'`output` doit être exactement
celui que `virsh` liste. Un output écrit en dur passerait le premier contrôle et
tomberait sur le second.

## Le nettoyage est un test, pas une politesse

Le dernier test déroule le `destroy` et exige que **rien ne survive**, ni dans
l'état ni sur l'hôte. Il s'exécute même si les tests précédents ont échoué :
sans cela, un lab raté laisserait un volume derrière lui, et c'est le lab
suivant qui en paierait le prix.

## À vous de jouer

```bash
dsoxlab run first-infra-first-infrastructure
dsoxlab check first-infra-first-infrastructure
dsoxlab hint first-infra-first-infrastructure
```

**Prérequis** : `libvirtd` joignable en `qemu:///system`, votre utilisateur dans
le groupe `libvirt`, le pool `default` défini et démarré, `terraform` et `virsh`
dans le `PATH`. Le réseau n'est nécessaire que pour le premier `init`.

Sous-objectif d'examen visé : **1c**, déroulé dans un cycle complet **1a**
`init`, **1b** `plan`, **1c** `apply`, **1d** `destroy`.

Référence : [première infrastructure](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/premiere-infrastructure/)
