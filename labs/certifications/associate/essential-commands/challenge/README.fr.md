# 🎯 Challenge : les commandes que l'examen attend, faites plutôt que récitées

## 📦 Le point de départ

`challenge/work` n'est pas initialisé. Il contient une configuration qui ne
tient pas debout, et un fichier que personne n'a créé avec Terraform.

| Fichier | Ce qu'il a |
| --- | --- |
| `versions.tf` | complet. Trois providers locaux, aucune VM, aucun compte cloud |
| `variables.tf` | complet. Une variable par marche de la cascade |
| `main.tf` | **mal indenté** et troué par un `???` |
| `outputs.tf` | cinq sorties, toutes trouées |
| `terraform.tfvars` | vide, à remplir |
| `env.auto.tfvars` | vide, à remplir |
| `etat/preexistant.txt` | **existe déjà sur le disque**, et attend d'être adopté |

Aucun `.terraform/`, aucun état, aucun répertoire `preuves/`.

## ✅ Ce qu'il faut obtenir

1. **`preuves/codes.json`** consigne les codes de retour de six gestes, relevés
   au moment où vous les faites :

   | Clé | Le geste |
   | --- | --- |
   | `validate_avant_init` | `validate` lancé avant tout `init` |
   | `validate_configuration_valide` | `validate` sur la configuration réparée |
   | `validate_attribut_absent` | `validate` sur une variante portant un attribut qui n'existe dans aucun schéma |
   | `fmt_check_avant` | `fmt -check` sur le `main.tf` mal indenté |
   | `fmt_check_apres` | `fmt -check` une fois reformaté |
   | `plan_avant_convergence` | `plan -detailed-exitcode` avant le premier apply |

2. La configuration **converge** : `plan -detailed-exitcode` sort en 0, et
   `fmt -check -recursive` aussi.

3. Les quatre premiers outputs désignent le gagnant de la cascade de
   précédence. Chaque variable est posée par **plusieurs sources à la fois** :
   une seule gagne, et le nom de la valeur dit laquelle.

   Les variables d'environnement à poser, qui font partie de l'énoncé :

   ```bash
   export TF_VAR_par_environnement="gagnant-environnement"
   export TF_VAR_par_fichier="perdant-environnement"
   export TF_VAR_par_ligne_de_commande="perdant-environnement"
   ```

   À vous de répartir le reste entre `terraform.tfvars`, `env.auto.tfvars` et
   `-var` pour que chaque output rende la valeur `gagnant-<sa source>`.

4. Un bloc **`moved`** a renommé `random_pet.ancien_nom`, et il a été
   **appliqué** : l'ancienne adresse ne figure plus dans l'état.

5. Un bloc **`import`** a fait passer `terraform_data.provisionne_ailleurs`
   sous gestion, avec son identifiant existant, `identifiant-connu`.

6. Un bloc **`removed`** a retiré `local_file.adopte` de l'état **sans détruire
   le fichier** : `etat/preexistant.txt` est toujours là, avec son contenu.

7. **`preuves/plan-replace.json`** est un plan enregistré qui demande le
   remplacement de `null_resource.a_remplacer`, et de rien d'autre.

8. `identifiant_sensible` est marqué **sensible**.

## ⚠️ Le cœur du sujet

Deux choses se paient cher le jour de l'examen.

**`validate` n'est pas un correcteur orthographique.** Il a besoin des
**schémas** des providers : lancé avant `init`, il ne valide rien et le dit par
un code non nul. Une fois les schémas en place, il attrape un attribut qui
n'existe pas, ce que « il ne vérifie que la syntaxe » laissait croire
impossible.

**`fmt -check` rend 3, pas 1.** Un script de CI qui testerait `-eq 1`
laisserait passer tous les fichiers hors format.

Et une troisième, qui surprend en écrivant le lab : **`init` parse la
configuration**. Il échoue donc sur un `???`, avec un message qui parle
d'opérateur ternaire et envoie chercher au mauvais endroit. Réparez le `???`
avant d'initialiser.

Enfin, `removed` sans `lifecycle { destroy = false }` **détruit** l'objet au
lieu de le rendre. Un mot d'écart, et le fichier est perdu.

## 🔍 Validation

`dsoxlab check certifications-associate-essential-commands` prouve, par
exécution :

- que les six codes de `codes.json` sont ceux que **votre** configuration
  produit : les tests rejouent les six gestes dans des copies jetables et
  comparent. Un chiffre recopié de travers tombe ;
- que chaque marche de la cascade désigne bien son gagnant, lu dans
  `output -json` ;
- que `moved` a été **appliqué**, et pas seulement planifié ;
- que la ressource importée porte l'identifiant existant, et n'a donc pas été
  créée ;
- que `removed` a laissé le fichier **intact sur le disque** pendant que l'état
  l'oubliait ;
- que le plan de remplacement vise une seule adresse, en `delete` puis
  `create` ;
- que la valeur sensible est masquée à l'écran **et lisible en clair dans
  l'état** : `sensitive` cache un affichage, il ne chiffre rien ;
- qu'au bout du compte la configuration converge et tient le format canonique.

Aucun test n'ouvre votre `main.tf`, et aucun ne lit un message destiné à un
humain.

Bloqué ? `dsoxlab hint certifications-associate-essential-commands`.
