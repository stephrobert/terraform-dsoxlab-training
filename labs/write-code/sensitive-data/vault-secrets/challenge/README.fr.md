# 🎯 Challenge : le secret vient de Vault, sans toucher le state

## ✅ Objectif

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

## 🔍 Validation

`dsoxlab check write-code-sensitive-data-vault-secrets` prouve, sur du JSON et via
l'API Vault :

- aucune entrée `mode: data` ; la réplique a `data_json_wo`, `data_json` à `null`
  et `data` vide, `data_json_wo_version` à `1` ;
- le mot de passe source n'apparaît **nulle part** dans `show -json` ni le state ;
- `kvv2/app/db-replique` dans Vault contient le **même** mot de passe que la
  source ;
- idempotence, et rotation : `copie_version=2` pousse le nouveau mot de passe.

Bloqué ? `dsoxlab hint write-code-sensitive-data-vault-secrets`.
