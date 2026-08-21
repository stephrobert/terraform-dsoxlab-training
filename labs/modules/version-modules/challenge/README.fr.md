# 🎯 Challenge : trois versions publiées, trois façons de les consommer

## 📦 Le point de départ

`challenge/work` contient une bibliothèque et trois projets, tous **hors ligne**,
sans aucun provider :

| Dossier | Ce que c'est |
| --- | --- |
| `modules-src/etiquette/` | le module en **1.0.0**, à faire évoluer. **Pas encore** un dépôt Git |
| `modules-src/CHANGELOG.md` | une seule entrée, deux manquent |
| `fige/` | `source` troué, doit rester sur la 1.0.0 |
| `stable/` | `source` troué **et** une ligne `version` de trop |
| `migre/` | `source` troué, arguments à adapter |
| `CIBLE.md` | ce que chaque version doit apporter, et ce que chaque projet doit viser |

## ✅ Objectif

Publier **trois** versions du module, puis brancher les trois projets dessus avec
la forme de référence qui convient à chacun.

## 📋 Ce qu'il faut obtenir

1. `modules-src` est un dépôt Git avec **trois tags annotés** sur **trois commits
   distincts** : `v1.0.0`, `v1.1.0`, `v2.0.0`.
2. La `1.1.0` ajoute une variable `suffixe` **facultative**, garde `prefixe`, et
   sa sortie `version_module` vaut `1.1.0`.
3. La `2.0.0` **renomme** `prefixe` en `nom_projet`, et `version_module` vaut
   `2.0.0`.
4. `fige/` vise la référence **immuable** du commit de la 1.0.0, et expose
   `version_module = "1.0.0"`.
5. `stable/` vise le tag `v1.1.0`, **sans** argument `version`, et expose
   `etiquette = "atelier-nord"`.
6. `migre/` vise le tag `v2.0.0`, arguments adaptés, et expose
   `etiquette = "chantier"`.
7. Les trois projets sont **appliqués**.

## ⚠️ Le cœur du sujet

Un tag Git **se déplace** : `git tag -f` change le commit désigné sans que rien
ne bouge côté consommateur, et un `terraform init -upgrade` ramène alors un autre
code **sous le même numéro**. Une seule référence ne peut pas être redéfinie.

| Forme de `?ref=` | Ce qu'elle garantit |
| --- | --- |
| absente | rien : la **branche par défaut**, qui bouge à chaque commit |
| un tag (`v1.1.0`) | la version **publiée**, tant que personne ne déplace le tag |
| un **SHA-1** | le **contenu**, définitivement |

Et l'argument `version` n'existe **que** pour un module de registre. À côté d'une
source Git, l'`init` s'arrête sur `Invalid registry module source address`.

Le dépôt est local : la source est donc une URL `git::file://`. Construisez-la
avec `path.cwd` pour qu'elle ne dépende pas de votre arborescence.

## 🔍 Validation

`dsoxlab check modules-version-modules` prouve, par exécution :

- les trois `.terraform/modules/modules.json`, écrits par Terraform : leur
  `Source` donne la référence **réellement résolue**, et un `?ref=` de 40
  caractères hexadécimaux distingue un SHA-1 d'un nom de tag ;
- l'absence de clé `Version` dans ces entrées, réservée aux modules de registre ;
- `terraform output -json` : `version_module` vient du module résolu, il ne peut
  pas être écrit depuis la racine ;
- le code **installé** sous `.terraform/modules/` : la 1.1.0 doit encore déclarer
  `prefixe` et déclarer `suffixe` **avec** un `default`, la 2.0.0 doit déclarer
  `nom_projet` et plus `prefixe`.

Aucun test ne lit vos fichiers `.tf`.

Bloqué ? `dsoxlab hint modules-version-modules`.
