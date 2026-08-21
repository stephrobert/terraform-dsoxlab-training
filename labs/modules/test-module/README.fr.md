# Une suite de tests qui ne peut pas échouer ne prouve rien

`terraform test` exécute des fichiers `.tftest.hcl` contre la configuration du
**répertoire courant**. Un module se teste donc **depuis son propre répertoire**,
sans configuration racine enveloppante : les sorties du module s'y lisent
directement par `output.<nom>`.

## L'anatomie d'une suite

```hcl
variables {
  prefixe = "atelier"
}

run "defaut" {
  assert {
    condition     = output.etiquette == "atelier"
    error_message = "Sans suffixe, l'etiquette doit valoir le prefixe seul."
  }
}
```

Trois niveaux à distinguer. Le bloc `variables` de **niveau fichier** s'applique à
tous les `run`. Un bloc `variables` **dans un `run`** l'emporte pour ce run-là. Et
chaque `run` peut porter plusieurs `assert`, chacun avec son `error_message`, qui
est ce que vous lirez en cas d'échec.

## `apply` par défaut, `plan` sur demande

Un `run` **applique** par défaut : « By default, each `run` block executes with
`command = apply` ». C'est ce qui permet d'assérer des valeurs calculées à partir
de ressources réellement créées, et c'est aussi ce qui les crée **pour de vrai** :

```text
$ ls -A plaques
      ← vide : le fichier a bien ete cree, puis detruit au teardown
```

Le répertoire, lui, reste. Retenez que `terraform test` **crée** de
l'infrastructure et la détruit à la fin, ce que la documentation dit sans détour :
« This command creates real infrastructure and will attempt to clean up the
testing infrastructure on completion. »

Quand seul le **plan** vous intéresse, dites-le :

```hcl
run "verifie_sans_creer" {
  command = plan

  assert {
    condition     = output.etiquette == "atelier"
    error_message = "L'etiquette calculee au plan doit deja etre correcte."
  }
}
```

## Prouver un refus : `expect_failures`

Un module sérieux **refuse** les entrées invalides. Ce comportement ne s'asserte
pas, puisque rien ne doit être produit : il se **déclare**.

```hcl
run "prefixe_trop_court_refuse" {
  command = plan

  variables {
    prefixe = "ab"
  }

  expect_failures = [var.prefixe]
}
```

Le run passe **parce que** la validation a rejeté la valeur. Si vous retirez la
`validation` du module, le même run échoue, et le message est explicite :

```text
Error: Missing expected failure

The checkable object, var.prefixe, was expected to report an error but did
not.
```

C'est la seule forme qui teste la **garde** d'un module. Une réserve utile :
`expect_failures` ne couvre que les objets de la configuration testée, pas ceux
d'un module enfant.

## Enchaîner les `run`

Les `run` d'un fichier s'exécutent **en séquence** et partagent leur contexte. Un
`run` peut donc préparer le terrain pour le suivant, en exécutant une **autre**
configuration :

```hcl
run "prepare_le_prefixe" {
  module {
    source = "./prefixe"
  }
}

run "utilise_le_prefixe_prepare" {
  variables {
    prefixe = run.prepare_le_prefixe.valeur
  }

  assert {
    condition     = output.etiquette == "ATELIER"
    error_message = "L'etiquette doit reprendre le prefixe prepare."
  }
}
```

Le bloc `module` d'un `run` n'accepte que `source` et `version` : tout autre
argument est refusé sur `An argument named "..." is not expected here`. Les
sorties du run précédent se lisent par `run.<nom>.<sortie>`.

## Ce que rend `terraform test`

Le code de retour vaut **0** si tout passe, **1** dès qu'un run échoue. C'est le
seul contrat exploitable en intégration continue, et la sortie humaine ne s'y
substitue pas. Pour automatiser, lisez le flux **JSONL** :

```bash
terraform test -json
```

```json
{"type":"test_summary","test_summary":{"status":"pass","passed":4,"failed":0,"errored":0,"skipped":0}}
```

Les types d'événements sont `version`, `test_abstract`, `test_file`, `test_run` et
`test_summary`. L'option `-verbose` y ajoute `test_state` pour les runs en `apply`
et `test_plan` pour ceux en `plan`.

## Deux pièges mesurés

Un **`-filter` qui ne correspond à aucun fichier** ne produit aucune erreur :

```text
$ terraform test -filter=tests/inexistant.tftest.hcl
Success! 0 passed, 0 failed.
```

Code de retour **0**. Une CI qui se contente de ce code peut donc être verte sans
avoir rien testé, et c'est exactement ce qui arrive quand un chemin de filtre
change.

Ensuite, un **échec d'assertion** n'arrête pas le fichier : les `run` suivants
s'exécutent quand même. Une **erreur**, en revanche, les fait passer en `skip` :

```text
  run "defaut"... fail            ← assertion fausse, la suite continue
  run "avec_suffixe"... pass

  run "defaut"... fail            ← erreur de reference, la suite s'arrete
  run "avec_suffixe"... skip
```

## `init` reste nécessaire, parfois

Sur un module autonome, sans provider ni module appelé, `terraform test` fonctionne
sans `init`. Dès que la configuration **appelle un module** ou déclare un
**provider**, il faut l'installer d'abord :

```text
Error: Module not installed

This module is not yet installed. Run "terraform init" to install all modules
required by this configuration.
```

## À vous de jouer

Vous savez où vit une suite, comment couvrir un défaut, une option et un refus, et
comment lire le résultat en machine. Le challenge vous fait écrire la suite d'un
module complet, et vérifie qu'elle **détecte** une régression : chaque
comportement est cassé à tour de rôle dans une copie du module, et votre suite
doit tomber.

```bash
dsoxlab run modules-test-module
dsoxlab check modules-test-module
dsoxlab hint modules-test-module
```

Il se joue **hors ligne**, sans aucun provider.

Sous-objectif d'examen visé : **4d** (tester un module).

Référence : [tester un module](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/tester-module/)
