# `terraform state show` : une fiche pour vos yeux, pas pour un script

`terraform state show <adresse>` affiche la fiche d'**une** instance enregistrée
dans le state. C'est la lecture de confort après un `terraform state list`. Mais
la documentation officielle est nette : cette sortie est destinée à la
**consommation humaine**, pas programmatique. Ce tutoriel montre ce qu'elle
affiche, surtout ce qu'elle **cache**, et par quoi la remplacer dès qu'un script
en dépend.

## Une instance à la fois, et l'adresse doit être exacte

La commande n'accepte qu'une seule adresse, et cette adresse doit désigner **une
instance précise**. C'est le premier mur après un `state list` :

```bash
terraform state show random_pet.noeud
```

```text
No instance found for the given address!

This command requires that the address references one specific instance.
To view the available instances, use "terraform state list". Please modify
the address to reference a specific instance.
```

Le code de retour vaut **1**. Sur une ressource créée avec `count` ou
`for_each`, il faut donc l'index ou la clé :

```bash
terraform state show 'random_pet.noeud[1]'
terraform state show 'random_pet.zone["eu-west"]'
terraform state show data.local_file.lecture
```

Les guillemets simples ne sont pas décoratifs : sous `zsh`, les crochets sont un
motif de nom de fichier et la commande échoue avant même d'atteindre Terraform.

## Ce que la fiche affiche

Pour une ressource sans surprise, la fiche est directement lisible :

```bash
terraform state show random_pet.env
```

```text
# random_pet.env:
resource "random_pet" "env" {
    id        = "happy-lizard"
    length    = 2
    separator = "-"
}
```

Trois attributs, et c'est tout. Retenez ce nombre : le state en contient
**cinq**.

## Le premier angle mort : les attributs nuls disparaissent

Un attribut à `null` est **omis** de la fiche. Il existe pourtant bel et bien
dans le state, et la sortie JSON le montre :

```bash
terraform show -json | jq '.values.root_module.resources[]
  | select(.address == "random_pet.env") | .values'
```

```json
{
  "id": "happy-lizard",
  "keepers": null,
  "length": 2,
  "prefix": null,
  "separator": "-"
}
```

`keepers` et `prefix` n'apparaissaient nulle part dans la fiche. Conséquence
directe : un `grep keepers` sur la sortie de `state show` renvoie du vide, et
l'on en conclut à tort que l'attribut n'est pas supporté par le provider. La
bonne question n'est pas « le provider le connaît-il », mais « vaut-il `null` ».

## Le second angle mort : les valeurs sensibles sont caviardées

Un attribut sensible est remplacé par un marqueur :

```bash
terraform state show random_password.api
```

```text
# random_password.api:
resource "random_password" "api" {
    bcrypt_hash = (sensitive value)
    id          = "none"
    length      = 24
    ...
    result      = (sensitive value)
}
```

C'est une protection utile : la fiche peut être montrée à quelqu'un sans fuiter
le secret. Mais elle rend la valeur inatteignable par ce chemin. Pour savoir
**quels** attributs Terraform considère comme sensibles, le JSON porte un objet
dédié :

```bash
terraform show -json | jq '.values.root_module.resources[]
  | select(.address == "random_password.api") | .sensitive_values'
```

```json
{
  "bcrypt_hash": true,
  "result": true
}
```

## La bascule vers le JSON, et son revers

Dès qu'une valeur doit servir ailleurs que sous vos yeux, la doc désigne la voie
correcte : une sortie JSON, puis décodage de la structure documentée.

Attention, la réponse a **changé de version**, et beaucoup de tutoriels en ligne
sont restés à l'ancienne. Jusqu'à Terraform 1.15 inclus, `terraform state show`
n'acceptait pas `-json` :

```bash
terraform state show -json random_pet.env
```

```text
Failed to parse command-line flags
flag provided but not defined: -json
```

Depuis la **1.16**, ce drapeau existe et la commande rend un document JSON.
Vérifiez donc votre version avant de recopier une réponse trouvée ailleurs :

```bash
terraform version
```

La distinction qui, elle, ne bouge pas, est celle du **périmètre** :

| Commande | Ce qu'elle rend |
|---|---|
| `terraform state show -json <adresse>` | **une** ressource, depuis la 1.16 |
| `terraform show -json` | le state **entier**, ses outputs compris |

Pour une valeur unique on a désormais le choix ; pour une vue d'ensemble, c'est
toujours `terraform show -json`, sans `state`.

Le revers est important : **le JSON expose les valeurs sensibles en clair**. La
page officielle le dit sans détour, « any sensitive values in Terraform state
will be displayed in plain text ». Là où `state show` protège, `show -json`
révèle. Un `terraform show -json` redirigé vers un artefact de pipeline y dépose
donc vos secrets.

## Le troisième piège : `state show` ne rafraîchit rien

La commande lit **le state enregistré**. Elle n'interroge pas l'infrastructure.
Modifiez un objet hors de Terraform, puis relancez la fiche : elle est
**inchangée**, empreintes comprises. C'est le `terraform plan` suivant, qui
rafraîchit, qui révèle la dérive et sort en code **2** avec
`-detailed-exitcode`.

`state show` montre donc l'écart entre le state et votre code, **jamais** entre
le state et la réalité. Le distinguer évite de conclure « tout va bien » sur une
ressource modifiée dans le dos de Terraform.

## À vous de jouer

Vous savez qu'il faut une adresse d'instance, index compris ; que la fiche omet
les attributs nuls et caviarde les sensibles ; que `terraform show -json` est la
seule voie fiable pour un script, au prix d'exposer les secrets ; et que
`state show` ne rafraîchit rien. Le challenge vous fait remplir cinq outputs qui
ne peuvent venir que du state, dont deux valeurs que la fiche humaine refuse de
montrer.

```bash
dsoxlab run state-terraform-state-show
dsoxlab check state-terraform-state-show
dsoxlab hint state-terraform-state-show
```

Sous-objectif d'examen visé : **1e** (inspecter et manipuler le state), niveau
Associate.

Référence : [terraform state show](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-show/)
