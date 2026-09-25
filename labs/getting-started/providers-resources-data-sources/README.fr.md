# Ce que Terraform gère, ce qu'il se contente de lire

Un mot sépare les deux natures de blocs, et il décide de tout : `resource` crée
et gère, `data` lit. Tant qu'on n'a pas vu un `destroy` effacer les objets gérés
sans toucher à ce que la data source lisait, on croit qu'un bloc `data` est une
resource en lecture seule.

Ce lab impose les deux conséquences réelles, et elles ne sont pas symétriques.

## La preuve tient dans un champ du state

```console
$ terraform show -json | jq -r '.values.root_module.resources[] | "\(.mode)\t\(.address)"'
data     data.local_file.catalogue
managed  local_file.resume
managed  null_resource.sceau
managed  random_pet.empreinte
```

`mode` ne se discute pas : un bloc créé sort en `managed`, un bloc de lecture en
`data`. C'est ce champ, et non la lecture des `.tf`, que le lab interroge.

La référence change avec la nature, et le préfixe est le seul indice :

| Nature | Référence |
| --- | --- |
| `resource "local_file" "resume"` | `local_file.resume.filename` |
| `data "local_file" "catalogue"` | `data.local_file.catalogue.content` |

## Première conséquence : le destroy ne touche pas ce qu'il n'a pas créé

```console
$ terraform destroy -auto-approve
$ ls resume.txt catalogue.txt
ls: cannot access 'resume.txt': No such file or directory
catalogue.txt
```

Le fichier géré disparaît, celui qui était seulement lu reste, **octet pour
octet**. C'est ce qui rend un bloc `data` utilisable sur une ressource dont on
n'est pas propriétaire.

## Seconde conséquence : une data source est relue à chaque plan

C'est celle qu'on ne voit pas venir. Sans toucher une ligne de HCL :

```console
$ terraform plan -detailed-exitcode ; echo $?
0
$ echo "revision=4" >> catalogue.txt
$ terraform plan -detailed-exitcode ; echo $?
2
```

Une data source n'est pas un cache. Elle est relue à chaque plan, et ce qu'elle
irrigue bouge avec elle. Un `0` dans ce second cas voudrait dire que la valeur
lue n'alimente rien.

C'est la cause la plus fréquente d'un plan qui bouge « tout seul » : quelqu'un a
modifié, ailleurs, une donnée que la configuration lit.

## La dépendance vient de la référence, jamais d'un `depends_on`

```hcl
resource "null_resource" "sceau" {
  triggers = {
    empreinte = random_pet.empreinte.id
    catalogue = data.local_file.catalogue.content
  }
}
```

Deux dépendances, zéro `depends_on`. Terraform construit son graphe à partir des
références qu'il trouve dans les expressions : citer un attribut suffit, et c'est
la forme que la documentation préfère.

Notez que `random_pet.empreinte.id` n'existe **qu'après création**. La référencer
est la seule façon de l'obtenir : aucune valeur écrite à la main ne pourrait la
deviner.

## La contrainte de version, et son piège à deux composants

```hcl
local = { source = "hashicorp/local", version = "~> 2.5" }
```

L'opérateur pessimiste laisse flotter le composant le plus à **droite** de ce qui
est écrit :

| Contrainte | Accepte | Refuse |
| --- | --- | --- |
| `~> 2.5` | 2.9 | 3.0 |
| `~> 2.5.0` | 2.5.9 | 2.6.0 |

Avec deux composants, c'est donc le **mineur** qui flotte, ce qui n'est pas ce
que la plupart des gens croient écrire.

## À vous de jouer

```bash
dsoxlab run getting-started-providers-resources-data-sources
dsoxlab check getting-started-providers-resources-data-sources
dsoxlab hint getting-started-providers-resources-data-sources
```

Il se joue **hors ligne**, sur `local`, `null` et `random`, `local` fournissant
justement une resource **et** une data source du même nom.

Sept tests. Le dernier joue le `destroy` dans une **copie** du répertoire : le
lab reste ainsi rejouable sans tout réappliquer.

Sous-objectif d'examen visé : **2b**, avec appui sur **5b**.

Référence : [providers, ressources et data sources](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/providers-resources-data-sources/)
