# Le secret vient de Vault, le state n'en saura rien

## La situation

**Sous-objectif d'examen visé : 2f (gérer les données sensibles), le seul sous-objectif qui cite nommément Vault.**

Les labs voisins traitent le secret que l'on fabrique ou que l'on saisit. Celui-ci traite le secret que l'on va **chercher ailleurs**. Le piège est que la voie historique, la data source `vault_kv_secret_v2`, recopie la valeur en clair dans le state, et que `sensitive_values` la marque `true` sans rien cacher : le mot de passe reste lisible dans `terraform show -json`. On veut au contraire qu'il ne laisse **aucune trace**.

## Capacité visée

Consommer un secret préexistant dans Vault depuis Terraform, en le faisant transiter jusqu'à son destinataire sans qu'il laisse la moindre trace dans le state ni le plan. Lire la source par un bloc **`ephemeral`** (jamais persisté), écrire la destination par un argument **write-only** (`data_json_wo`), et piloter la rotation par un entier de version, seule chose qui subsiste.

## D'où part l'apprenant

`challenge/work` vise un serveur **Vault dev** que dsoxlab démarre automatiquement (`runtime.services`) : aucune installation, aucun compte, jeton racine `root` sur `http://127.0.0.1:8200`. Le secret source `kvv2/app/db` (clés `password` et `username`) est **déposé** dans Vault avant les tests ; sous `dsoxlab run`, l'apprenant le dépose lui-même avec la CLI `vault` (voir le challenge). Le secret **préexiste** : Terraform ne le crée pas, il le consomme.

Sont complets : `versions.tf` (provider `hashicorp/vault` en `>= 5.0`, `required_version >= 1.11`), `providers.tf` (adresse et jeton du Vault dev), `variables.tf` (`copie_version`, défaut 1). Seul `main.tf` est troué :

```hcl
??? "vault_kv_secret_v2" "source" {   # lire la source SANS la persister
  mount = ???
  name  = ???
}
resource "vault_kv_secret_v2" "replique" {
  mount = "kvv2"
  name  = "app/db-replique"
  ???   = jsonencode({ password = ??? })   # ecrire SANS persister (write-only)
  ???   = var.copie_version                # l'entier de version write-only
}
output "chemin" { value = ??? }
```

## L'état à atteindre

1. Le secret source est lu par un bloc `ephemeral`, qui ne produit **aucune** entrée dans le state, ni en `mode: managed`, ni en `mode: data`.
2. La réplique est une ressource `mode: managed` dont `data_json_wo` vaut `null`, `data_json` vaut `null`, `data` est un objet vide, et `data_json_wo_version` porte un nombre.
3. La valeur du mot de passe source n'apparaît **nulle part** dans `terraform show -json` ni dans `terraform.tfstate`.
4. Le secret a pourtant bien transité : `kvv2/app/db-replique` existe dans Vault et contient le même mot de passe que `kvv2/app/db`.
5. Juste après l'apply, un nouveau plan ne propose rien. Changer le mot de passe source dans Vault **sans** toucher `copie_version` ne produit toujours aucun plan.
6. Porter `copie_version` à 2 produit un plan non vide, et l'apply correspondant pousse le nouveau mot de passe dans la réplique.

## Comment on le prouve

Les tests n'ouvrent aucun `.tf` de l'apprenant. Ils pilotent Terraform dans `challenge/work` et n'exploitent que du JSON, le fichier de state brut, des codes retour, et l'état réel de Vault interrogé par son API.

1. Garde d'entrée : si Vault est injoignable, la suite est mise en `skip` (ou en échec sous `LAB_WORKDIR`). Puis le secret source est déposé par l'API.
2. `show -json` après apply : aucun `mode: data`, une seule entrée `mode: managed` de type `vault_kv_secret_v2`, dont `data == {}`, `data_json is None`, `data_json_wo is None`, `data_json_wo_version == 1`.
3. Le mot de passe source, lu par l'API, est cherché dans `show -json` **et** dans le state brut : zéro occurrence.
4. `GET /v1/kvv2/data/app/db-replique` renvoie le même `password` que la source.
5. `plan -detailed-exitcode` rend 0 après apply, et encore 0 après un changement du secret source sans incrément de version.
6. `plan -detailed-exitcode -var copie_version=2` rend 2 ; après `apply -var copie_version=2`, l'API Vault donne le nouveau mot de passe dans la réplique.

## 🎯 Challenge : le secret vient de Vault, sans toucher le state

### ✅ Objectif

Dans `challenge/work`, complétez `main.tf` pour **répliquer** le secret
`kvv2/app/db` vers `kvv2/app/db-replique`, sans que le mot de passe touche jamais
le state Terraform.

Un serveur **Vault dev** est démarré tout seul par dsoxlab (`runtime.services`).
Pour un `dsoxlab run` manuel, déposez d'abord le secret source :

```bash
export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root
vault secrets enable -path=kvv2 kv-v2
vault kv put kvv2/app/db username=app password=change-me
```

(`dsoxlab check` le dépose automatiquement avant ses tests.)

Puis remplissez les `???` de `main.tf` :

1. le **bloc de lecture éphémère** du secret source (`mount = "kvv2"`,
   `name = "app/db"`) ;
2. l'argument **write-only** qui écrit le password dans la réplique, en reprenant
   la valeur lue de façon éphémère ;
3. le **numéro de version** write-only (`= var.copie_version`) ;
4. la valeur de l'output `chemin` (le `mount/name` de la réplique).

### 🔍 Validation

`dsoxlab check write-code-sensitive-data-vault-secrets` prouve, sur du JSON et via
l'API Vault :

- aucune entrée `mode: data` ; la réplique a `data_json_wo`, `data_json` à `null`
  et `data` vide, `data_json_wo_version` à `1` ;
- le mot de passe source n'apparaît **nulle part** dans `show -json` ni le state ;
- `kvv2/app/db-replique` dans Vault contient le **même** mot de passe que la
  source ;
- idempotence, et rotation : `copie_version=2` pousse le nouveau mot de passe.

Bloqué ? `dsoxlab hint write-code-sensitive-data-vault-secrets`.
