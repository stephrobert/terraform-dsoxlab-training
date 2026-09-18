# Le workflow Terraform : lire un plan avant de l'appliquer

`init`, `plan`, `apply`, `destroy` : quatre commandes qu'on récite. Le workflow
n'est pas cette liste. Il tient dans une seule question, posée **avant** de
toucher à quoi que ce soit : parmi mes ressources, lesquelles seront modifiées
en place, et lesquelles seront **détruites puis recréées** ?

La différence n'est pas cosmétique. Un remplacement fait disparaître un objet
existant, avec tout ce qu'il porte : une adresse IP, un mot de passe généré, un
volume. Et la sortie de `terraform plan` annonce les deux cas **dans le même
bloc de texte**.

## Le plan à l'écran n'est pas le plan qu'on applique

Voici le piège le plus courant du workflow :

```bash
terraform plan     # vous lisez quelque chose
terraform apply    # Terraform REPLANIFIE, et applique ce qu'il trouve alors
```

Entre les deux, le state a pu être rafraîchi, un collègue a pu appliquer, une
donnée a pu changer. Rien ne garantit que ce qui s'exécute est ce que vous avez
lu.

```bash
terraform plan -out=tfplan    # le plan est ENREGISTRÉ
terraform apply tfplan        # ce plan-là, sans replanification, sans confirmation
```

Le fichier produit est binaire et versionné : seul l'outil sait le relire. Une
fois appliqué, il devient **périmé**, et Terraform refuse de le rejouer.

## La seule lecture fiable est le JSON

```bash
terraform show -json tfplan > plan.json
```

Chaque entrée de `resource_changes` porte un champ `change.actions`. Il n'y a
que quelques valeurs possibles, et elles ne se confondent pas :

| Actions | Signification |
|---|---|
| `["no-op"]` | rien ne bouge |
| `["update"]` | **mise à jour en place** : le même objet, modifié |
| `["create"]` | création |
| `["delete"]` | destruction |
| `["delete", "create"]` | **remplacement** : l'objet disparaît, un autre naît |
| `["create", "delete"]` | remplacement aussi, avec `create_before_destroy` |

Les deux dernières lignes sont le point à retenir : **l'ordre change, le sens
non**. Un test qui ne chercherait que `["delete", "create"]` manquerait la
moitié des cas.

```bash
jq '.resource_changes[] | select(.change.actions != ["no-op"]) | {address, actions: .change.actions}' plan.json
```

## Ce qui force un remplacement

Un attribut est **ForceNew** ou il ne l'est pas, et cela se décide dans le
provider, pas dans votre code. Quelques exemples mesurés :

```hcl
resource "terraform_data" "configuration" {
  input = var.etiquette          # update en place
}

resource "terraform_data" "jeton" {
  triggers_replace = [var.etiquette]   # remplacement
}

resource "local_file" "rapport" {
  content = "etiquette : ${var.etiquette}\n"   # remplacement
}
```

`local_file` est instructif : **tout** y force un remplacement, jusqu'aux
permissions du fichier. Le provider ne sait pas modifier, il sait écrire.

Les `keepers` d'une ressource `random_*` et les `triggers` d'une
`null_resource` sont dans le même cas : ils existent précisément pour provoquer
un remplacement.

<Aside type="caution" title="Un plan se lit avant, pas après">
La trace d'un remplacement dans le plan est visible à l'œil nu une fois qu'on
sait où regarder : l'identifiant futur de la ressource est **inconnu**
(`after_unknown`). Un objet qui n'existe pas encore ne peut pas promettre son
identifiant. À l'inverse, une mise à jour en place conserve le sien : c'est le
même objet.
</Aside>

## À vous de jouer

Vous savez maintenant qu'un plan lu n'est pas un plan appliqué tant qu'il n'est
pas enregistré, que sa seule lecture fiable est le champ des actions en JSON,
qu'un remplacement s'écrit `delete`+`create` dans n'importe quel ordre, et que
ce qui force un remplacement se décide dans le provider.

Le challenge vous fait produire ce plan, le classer, et l'appliquer tel quel.

```bash
dsoxlab run getting-started-terraform-workflow
dsoxlab check getting-started-terraform-workflow
dsoxlab hint getting-started-terraform-workflow
```

Sous-objectif d'examen visé : **6d** (générer et relire un plan d'exécution).

Référence : [Le workflow Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/workflow-terraform/)
