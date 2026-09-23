# Providers, resources et data sources : qui possède quoi

Un provider, une resource, une data source : trois mots qu'on apprend le premier
jour, et dont la différence ne devient claire qu'au premier `destroy` mal
placé. Ce tutoriel la rend visible avant que ce `destroy` n'arrive.

## Le provider est le pilote

Un **provider** est un exécutable que Terraform télécharge et lance en
sous-processus. Il sait parler à un système : une API cloud, un système de
fichiers, une base de données. Terraform, lui, ne sait rien faire tout seul.

```hcl
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
```

`source` nomme l'organisation et le nom du provider. Sans lui, Terraform
**devine** sur son registre par défaut : la configuration s'applique quand même,
et n'est reproductible nulle part.

La contrainte `~> 2.5` est pessimiste : elle accepte `2.9`, refuse `3.0`. La
version majeure est verrouillée, les correctifs restent accessibles.

## La resource : Terraform en est propriétaire

Un bloc **`resource`** engage Terraform sur un cycle de vie complet. Il crée
l'objet, le modifie, et le **détruit** au `destroy`.

```hcl
resource "local_file" "resume" {
  content  = "..."
  filename = "${path.module}/resume.txt"
}
```

C'est un engagement, pas une description. Déclarer en `resource` un fichier que
quelqu'un d'autre a écrit, c'est se donner le droit de le supprimer.

## La data source : Terraform se contente de lire

Un bloc **`data`** interroge. Il ne crée rien, ne modifie rien, et n'apparaît
dans aucun `destroy`.

```hcl
data "local_file" "catalogue" {
  filename = "${path.module}/catalogue.txt"
}
```

Notez que c'est le **même** provider et le **même** type, `local_file`. Un seul
mot change, et deux cycles de vie opposés en découlent.

Le state garde la trace des deux, mais les distingue sans ambiguïté :

```bash
terraform show -json | jq '.values.root_module.resources[] | {mode, address}'
```

```text
{"mode": "data",    "address": "data.local_file.catalogue"}
{"mode": "managed", "address": "local_file.resume"}
{"mode": "managed", "address": "random_pet.reference"}
```

## Les références, et le graphe qu'elles construisent

La seule différence d'écriture est un préfixe :

| Vers | Syntaxe |
|---|---|
| une resource | `TYPE.NOM.ATTRIBUT` — `random_pet.reference.id` |
| une data source | `data.TYPE.NOM.ATTRIBUT` — `data.local_file.catalogue.content` |

Et elle suffit. Terraform construit son graphe à partir des **références qu'il
trouve dans les expressions** : pas de référence, pas d'arête, pas d'ordre
garanti. Un `depends_on` écrit à la main est presque toujours le symptôme d'une
référence manquante.

## Une data source est relue à chaque plan

C'est la conséquence qu'on oublie, et elle est très concrète :

```bash
echo "reference-05  onduleur  6 kVA" >> catalogue.txt
terraform plan -detailed-exitcode ; echo $?   # 2
```

**Aucun `.tf` n'a bougé**, et le plan n'est plus vide. La data source a été
résolue à nouveau, sa valeur a changé, et tout ce qui en dépend a bougé avec
elle.

Si le code retour est `0` ici, ce n'est pas que la data source ne se relit pas :
c'est que **personne ne s'en sert**. Une valeur lue qui n'irrigue rien ne se
voit jamais.

<Aside type="caution" title="Un déclencheur ne recopie pas un fichier">
Pour faire dépendre une ressource d'un fichier lu, préférez `content_sha1` à
`content`. L'empreinte change dès que le fichier change, et vous évitez de
recopier tout le contenu dans le state, qui n'est ni chiffré ni petit.
</Aside>

## Le `destroy`, et ce qu'il n'a pas le droit de toucher

```bash
terraform destroy -auto-approve
ls resume.txt      # disparu, Terraform l'avait créé
ls catalogue.txt   # intact, Terraform ne l'a jamais possédé
```

Voilà la démonstration complète. Écrivez `resource` au lieu de `data`, et le
second `ls` échoue : Terraform s'est cru propriétaire d'un fichier qu'il n'avait
jamais créé, et il l'a effacé.

## À vous de jouer

Vous savez maintenant qu'un provider se déclare avec sa source et une contrainte
pessimiste, qu'une `resource` engage Terraform jusqu'à la destruction, qu'une
`data` ne fait que lire, que le préfixe `data.` suffit à construire le graphe,
et qu'une data source relue peut faire bouger un plan sans qu'un seul `.tf` ait
changé.

Le challenge vous fait écrire les deux natures, puis prouver ce qu'un `destroy`
emporte et ce qu'il épargne.

```bash
dsoxlab run getting-started-providers-resources-data-sources
dsoxlab check getting-started-providers-resources-data-sources
dsoxlab hint getting-started-providers-resources-data-sources
```

Sous-objectif d'examen visé : **2b** (data sources), avec appui sur **5b**
(configuration et versionnement des providers).

Référence : [Providers, resources et data sources](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/providers-resources-data-sources/)
