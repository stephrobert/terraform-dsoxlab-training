# 🎯 Challenge : les fonctions définies par les providers

## ✅ Objectif

Dans `challenge/work`, rendez la configuration valide en utilisant **quatre
fonctions de provider** appelées par la syntaxe `provider::<nom_local>::<fonction>`.

Trois fichiers sont troués :

1. **`versions.tf`** : posez `required_version` (la version qui introduit la
   syntaxe qualifiée), déclarez le provider **intégré** sous le nom local
   **`tfcore`** (source `terraform.io/builtin/terraform`), et contraignez
   `hashicorp/local` à une version qui expose `direxists`.
2. **`locals.tf`** : cinq locals à remplir.
   - décoder `amont.tfvars.txt` en objet (les types sont restitués) ;
   - le ré-encoder en tfvars après y avoir ajouté `environment = "prod"` ;
   - produire la syntaxe d'expression de `config.zones` ;
   - tester l'existence d'un répertoire présent, puis d'un absent.
3. **`main.tf`** : le `content` du `local_file` est le tfvars ré-encodé.

Rappels :

- une fonction de provider n'existe que si le provider est **déclaré** dans
  `required_providers` (même `tfcore`), sinon `Unknown provider function` ;
- `direxists` a été **ajoutée dans une version précise** de `hashicorp/local` :
  une contrainte trop basse compile mais échoue à l'appel ;
- le nom du namespace est le **nom local** du provider, pas son type : ici
  `provider::tfcore::…`, pas `provider::terraform::…`.

## 🔍 Validation

`dsoxlab check write-code-provider-defined-functions` prouve, sur les sorties
JSON de Terraform :

- `providers schema -json` : les fonctions sont décrites par chaque provider ;
- `metadata functions -json` : aucune n'est une fonction du langage ;
- `version -json` : `hashicorp/local` est en 2.5.0 ou plus ;
- `output -json` : `node_count` est un **nombre**, `aval` est le tfvars trié,
  `zones_expr` est en syntaxe d'expression, `dir_present`/`dir_absent` valent
  vrai/faux ;
- `show -json` : le fichier écrit contient bien le tfvars ré-encodé.

Bloqué ? `dsoxlab hint write-code-provider-defined-functions`.
