# Lire des secrets depuis Vault sans les figer dans le state

L'examen Professional cite **nommément Vault** au sous-objectif **2f**. Le
problème n'est pas de lire un secret Vault, c'est de le lire **sans qu'il finisse
en clair dans le state**. Ce tutoriel montre le piège de la voie historique, puis
la bonne combinaison : lecture **éphémère** et écriture **write-only**. Le
challenge vous le fera prouver sur un secret répliqué.

## Le piège : la data source recopie le secret en clair

La façon la plus ancienne de lire un secret KV v2 est une **data source** :

```hcl
data "vault_kv_secret_v2" "source" {
  mount = "kvv2"
  name  = "app/db"
}
```

Elle fonctionne, mais elle **recopie la valeur dans le state**. Pire :
`sensitive_values` la marque `true` sans rien cacher, la valeur reste lisible dans
`terraform show -json` et dans `terraform.tfstate`. Le provider émet d'ailleurs un
**avertissement de dépréciation** sur cette data source. Un secret externe lu de
cette façon fuit exactement comme un secret codé en dur.

## La lecture éphémère : `ephemeral`

Le provider `hashicorp/vault` en **5.x** expose la même lecture sous forme
**éphémère**. Un bloc `ephemeral` produit une valeur disponible **pendant**
l'opération, mais **jamais écrite** dans le state ni le plan :

```hcl
ephemeral "vault_kv_secret_v2" "source" {
  mount = "kvv2"
  name  = "app/db"
}
```

On référence son résultat par `ephemeral.vault_kv_secret_v2.source.data["password"]`.
Cette valeur ne peut aller que dans un **contexte éphémère** : une config de
provider, un provisioner, ou un **argument write-only**. C'est ce dernier qui nous
intéresse.

## L'écriture write-only : `data_json_wo`

La ressource `vault_kv_secret_v2` a deux façons d'écrire son contenu :
l'argument ordinaire **`data_json`**, qui **persiste** dans le state (marqué
sensible, mais présent), et sa variante **write-only** **`data_json_wo`**, qui
transmet la valeur au provider **sans jamais la persister**. Comme tout write-only,
elle forme un couple obligatoire avec un numéro de version :

```hcl
resource "vault_kv_secret_v2" "cible" {
  mount = "kvv2"
  name  = "app/copie"

  data_json_wo         = jsonencode({ password = ephemeral.vault_kv_secret_v2.source.data["password"] })
  data_json_wo_version = 1
}
```

Après l'apply, dans le state : `data_json_wo` vaut `null`, `data_json` vaut
`null`, `data` est un objet vide ; seul **`data_json_wo_version`** subsiste. Pour
faire tourner le secret, on **incrémente** ce numéro. Le changer de `1` à `2`
redéclenche l'envoi ; sans ce changement, une nouvelle valeur dans la source
n'est **pas** reprise (Terraform ne suit pas ce qu'il ne stocke pas).

## Le duo éphémère + write-only

Bout à bout, le secret ne touche **jamais le disque côté Terraform** : lu par un
`ephemeral` (pas de state), écrit par un `data_json_wo` (pas de state). Il transite
en mémoire pendant l'opération, du KV source vers le KV cible. C'est la réponse
complète au sous-objectif 2f, et la seule qui ne laisse aucune trace.

## À vous de jouer

Vous savez que la data source `vault_kv_secret_v2` **fuit** (et est dépréciée),
qu'un bloc `ephemeral` lit sans persister, que `data_json_wo` écrit sans
persister, et que seul `data_json_wo_version` subsiste et pilote la rotation. Le
challenge vous fait répliquer un secret d'un chemin Vault vers un autre, en ne
laissant **aucune trace** dans le state. Un serveur Vault de développement est
démarré tout seul par dsoxlab.

```bash
dsoxlab run write-code-sensitive-data-vault-secrets
dsoxlab check write-code-sensitive-data-vault-secrets
dsoxlab hint write-code-sensitive-data-vault-secrets
```

Sous-objectif d'examen visé : **2f** (gérer les données sensibles), niveau
Professional.

Référence : [Provider Vault](https://registry.terraform.io/providers/hashicorp/vault/latest/docs)
