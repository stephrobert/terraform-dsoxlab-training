# Terraform, et ce qu'il garde en mémoire

On présente souvent Terraform comme « un outil qui lit des fichiers `.tf` et
appelle des API ». C'est vrai, et c'est insuffisant : cette description ne dit
pas pourquoi un second `apply` ne recrée rien, pourquoi supprimer un fichier à la
main provoque un plan non vide, ni pourquoi renommer une ressource dans le code
peut la **détruire**. Tout cela vient d'un seul objet, le **state**.

Ce tutoriel le montre sur une configuration purement locale : trois providers,
aucun compte cloud, aucun coût. Le challenge vous fera ensuite prouver chacun de
ces comportements.

## Le state n'est pas un cache

Un cache, on peut le jeter : les données se retrouvent à la source. Le state,
non. Il contient la **correspondance** entre une adresse dans votre code, par
exemple `local_file.rapport`, et un objet réel, identifié par son `id` chez le
provider. Jetez le state, et Terraform ne sait plus que cet objet lui
appartient : il proposera de le **créer à nouveau**.

```bash
terraform show -json | jq '.values.root_module.resources[] | {mode, type, address}'
```

```text
{"mode": "managed", "type": "random_pet",  "address": "random_pet.nom"}
{"mode": "managed", "type": "local_file",  "address": "local_file.rapport"}
{"mode": "data",    "type": "local_file",  "address": "data.local_file.inventaire"}
```

Deux modes cohabitent, et la distinction n'est pas décorative.

## managed contre data : ce que Terraform détruira

Une ressource en mode **`managed`** est sous la responsabilité de Terraform : il
l'a créée, il la modifiera, il la **détruira** au `destroy`. Une entrée en mode
**`data`** est seulement *lue* : elle est résolue à chaque plan, n'apparaît dans
aucun `destroy`, et sa disparition du code n'efface rien sur le disque.

```hcl
# Terraform crée ce fichier, et le supprimera.
resource "local_file" "rapport" {
  content  = "..."
  filename = "${path.module}/rapport.txt"
}

# Terraform lit ce fichier, et n'y touchera jamais.
data "local_file" "inventaire" {
  filename = "${path.module}/inventaire.txt"
}
```

La conséquence pratique est brutale : déclarer par erreur en `resource` un
fichier que quelqu'un a écrit à la main, c'est se donner le droit de le
supprimer. Un objet que personne n'a déclaré, lui, reste parfaitement invisible
pour Terraform. Il ne le surveille pas, ne le sauvegarde pas, et ne s'en plaindra
jamais.

## La référence, c'est la dépendance

Il y a deux façons d'écrire un fichier qui contient un nom généré. Elles
produisent le **même fichier sur le disque**, et elles ne valent pas la même
chose :

```hcl
# Non : la valeur est recopiée. Aucune dépendance, et si le nom change,
# le rapport ment.
content = "ressource generee : clever-mongrel\n"

# Oui : la valeur est CONSTRUITE. Terraform sait désormais que le rapport
# dépend du nom, et ordonne les opérations en conséquence.
content = "ressource generee : ${random_pet.nom.id}\n"
```

Terraform ne lit pas vos intentions : il construit un graphe à partir des
**références** qu'il trouve dans les expressions. Pas de référence, pas d'arête,
pas d'ordre garanti.

## L'idempotence se prouve par un code retour

« Le plan est vide » n'est pas une observation à faire à l'œil. La commande
répond par un code :

```bash
terraform plan -detailed-exitcode
echo $?
```

| Code | Signification |
|---|---|
| `0` | aucun changement : code, state et réalité sont alignés |
| `1` | erreur |
| `2` | des changements sont prévus |

C'est la forme à utiliser dans un script ou un test : elle ne dépend d'aucune
tournure de phrase, et elle ne bougera pas à la prochaine version.

## La dérive, et ce qui y survit

Supprimez le rapport hors de Terraform, puis demandez un plan. Terraform
rafraîchit d'abord son state, constate que l'objet a disparu, et propose de le
recréer. Ce qui compte, c'est **ce qu'il ne propose pas** :

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.resource_changes[] | {address, actions: .change.actions}'
```

```text
{"address": "local_file.rapport", "actions": ["create"]}
{"address": "random_pet.nom",     "actions": ["no-op"]}
```

Le `random_pet` est **intact**. C'est tout l'intérêt de la correspondance
stockée : sans elle, Terraform ne saurait pas que ce nom existe déjà, le
regénérerait, et le rapport recréé porterait un autre nom. La dérive se répare
là où elle a eu lieu, pas partout.

## sensitive masque l'affichage, et rien d'autre

Dernier point, et c'est le plus mal compris. Marquer une sortie `sensitive`
change **une seule chose** : ce que Terraform imprime à l'écran.

```hcl
output "nom_majuscule" {
  value     = upper(random_pet.nom.id)
  sensitive = true
}
```

```bash
terraform output
```

```text
nom_animal     = "clever-mongrel"
nom_majuscule  = <sensitive>
```

Ouvrez maintenant `terraform.tfstate` :

```json
"nom_majuscule": {"value": "CLEVER-MONGREL", "type": "string", "sensitive": true}
```

La valeur y est **en clair**. Le drapeau a bien été enregistré, mais il décrit
une intention d'affichage, pas une protection.

<Aside type="caution" title="Un fichier de state est une donnée sensible">
Tout ce que vos ressources manipulent finit dans le state, y compris les mots de
passe générés et les valeurs marquées `sensitive`. Un state se range comme un
secret : accès restreint, chiffrement au repos, jamais dans un dépôt git. Pour
qu'une valeur n'y entre pas du tout, c'est `ephemeral = true` qu'il faut, pas
`sensitive`.
</Aside>

## À vous de jouer

Vous savez maintenant que le state porte la correspondance entre le code et le
réel, que `managed` et `data` n'engagent pas la même responsabilité, qu'une
référence crée une dépendance là où une valeur recopiée n'en crée aucune, que
l'idempotence se lit dans un code retour, que la dérive épargne ce qui n'a pas
bougé, et que `sensitive` ne chiffre rien.

Le challenge vous fait établir ces six faits sur une configuration trouée, et les
tests les prouvent dans le JSON.

```bash
dsoxlab run getting-started-terraform-overview
dsoxlab check getting-started-terraform-overview
dsoxlab hint getting-started-terraform-overview
```

Sous-objectif d'examen visé : **1e** (state, import, dérive).

Référence : [Présentation de Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/presentation-terraform/)
