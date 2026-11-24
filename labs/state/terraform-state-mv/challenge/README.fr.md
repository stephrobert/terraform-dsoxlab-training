# Refactorer sans détruire, de `state mv` au bloc `moved`

## La situation

**Sous-objectif d'examen visé : 1e.**

Renommer un bloc ou le pousser dans un module vaut par défaut une destruction suivie d'une création : l'objet change d'identité. Ce lab traite le piège que la doc officielle signale et que les guides taisent : réconcilier le state à la main marche, mais ne laisse aucune trace rejouable par l'équipe, là où un bloc `moved` versionné fait la même chose en étant relu, revu et rejoué par tout le monde.

## Capacité visée

Rattacher des objets déjà créés à de nouvelles adresses sans les recréer : par `terraform state mv` quand le state est déjà désynchronisé du code, par un bloc `moved` quand le refactoring part du code, en prouvant dans les deux cas que les valeurs existantes ont survécu.

## D'où part l'apprenant

`challenge/work` contient une configuration déjà appliquée par « l'équipe précédente », dont le code a été refactoré sans que personne ne touche au state :

- `main.tf` : bloc `terraform` (`required_version = ">= 1.1"`, provider `hashicorp/random ~> 3.6`), les ressources `random_pet.frontend` et `random_integer.frontend_port`, et un appel `module "secret"` vers `./modules/secret`.
- `modules/secret/main.tf` : `random_password.this` et son output.
- `terraform.tfstate` : trois objets bien réels, mais aux **anciennes** adresses `random_pet.web`, `random_integer.web_port` et `random_password.db_secret`.
- `moved.tf` : squelette troué, un seul bloc, `from = ???` et `to = ???`.
- `.dsoxlab/etat-initial.tfstate` : copie figée du state de départ, lue par les tests comme référence des valeurs. À ne jamais modifier.
- Aucun `.terraform` : le `terraform init` est à la charge de l'apprenant.

Le premier `terraform plan` annonce 3 ressources à créer et 3 à détruire.

Deux méthodes sont imposées : les deux renommages se règlent en impératif avec `terraform state mv` (le code est déjà écrit, le state seul est en retard), le passage dans le module se règle en déclaratif avec le bloc `moved`, puis un plan enregistré et appliqué.

## L'état à atteindre

1. Les objets du state sont exactement aux adresses `random_pet.frontend`, `random_integer.frontend_port` et `module.secret.random_password.this` ; aucune des trois anciennes adresses ne subsiste.
2. Les valeurs enregistrées (nom, port, mot de passe) sont celles de `.dsoxlab/etat-initial.tfstate` : rien n'a été recréé au passage.
3. `terraform plan -detailed-exitcode` sort en code 0 : code et state convergent.
4. `challenge/work/moved.tfplan` existe et décrit l'entrée dans le module comme un **déplacement**, pas comme un couple destroy plus create.
5. Le bloc `moved` est toujours dans le code après l'apply : le supprimer est un changement cassant, la doc officielle recommande de conserver l'historique des déplacements.

## Comment on le prouve

- `terraform show -json` liste les objets `mode: managed` du module racine et des modules enfants : les tests comparent l'ensemble des adresses à l'attendu et vérifient l'absence des anciennes.
- Les valeurs de ce JSON sont confrontées à `.dsoxlab/etat-initial.tfstate`. Une seule divergence signe une recréation : `random_pet` et `random_password` tirent des valeurs neuves à chaque création.
- `terraform plan -detailed-exitcode` doit rendre 0 ; le code 2 signale des changements en attente, donc une réconciliation incomplète.
- `terraform show -json moved.tfplan` doit contenir un `resource_changes[]` dont `address` vaut `module.secret.random_password.this`, `previous_address` vaut `random_password.db_secret` et `change.actions` vaut `["no-op"]`. Terraform n'écrit `previous_address` que lorsqu'un bloc `moved` a été pris en compte : `state mv` ne le produit jamais. C'est le discriminant entre les deux méthodes, et il interdit de valider l'étape déclarative par un raccourci impératif.
- Rejeu : les tests copient `challenge/work` dans un répertoire temporaire, y ramènent l'objet à son ancienne adresse avec `terraform state mv module.secret.random_password.this random_password.db_secret`, puis enregistrent un nouveau plan. Le JSON doit à nouveau montrer un `no-op` porteur de `previous_address`. Bloc `moved` supprimé, ce plan repasse en destroy plus create et le test échoue : c'est exactement le « breaking change » décrit par la doc.
- Les deux renommages impératifs n'ont volontairement aucun bloc `moved` : leur seule preuve est la présence des valeurs d'origine aux nouvelles adresses, ce qu'un destroy plus create ne peut pas simuler.
- Aucun test ne lit le contenu des fichiers `.tf` de l'apprenant.

## 🎯 Challenge : rattacher trois objets existants, sans en détruire aucun

### ✅ Objectif

`challenge/work` contient un projet **déjà appliqué** par l'équipe précédente,
dont le code a été refactoré **sans que personne ne touche au state**. Les trois
objets existent, mais aux **anciennes** adresses :

| Dans le state (ancien) | Dans le code (nouveau) |
| --- | --- |
| `random_pet.web` | `random_pet.frontend` |
| `random_integer.web_port` | `random_integer.frontend_port` |
| `random_string.db_secret` | `module.secret.random_string.this` |

Commencez par mesurer les dégâts :

```bash
terraform init
terraform plan     # 3 to add, 0 to change, 3 to destroy
```

À vous de réconcilier, avec **la bonne méthode pour chaque cas** :

1. **Les deux renommages à la racine** se traitent en **impératif**, par
   `terraform state mv` : le code est déjà écrit, seul le state est en retard.
2. **Le passage dans le module** se traite en **déclaratif**, en complétant le
   bloc `moved` de **`moved.tf`** (le seul fichier à modifier), puis en appliquant.

Puis appliquez, et vérifiez que le plan ne propose plus rien.

**Ne supprimez pas le bloc `moved` après l'apply.** Il doit rester dans le code :
son retrait est un changement cassant, et les tests le vérifient.

Deux fichiers ne se touchent pas : `main.tf` et `modules/secret/main.tf` sont le
code refactoré, et `reference/etat-initial.tfstate` est la copie figée du state de
départ, qui sert de référence aux tests.

### 🔍 Validation

`dsoxlab check state-terraform-state-mv` prouve, par exécution :

- le state porte **exactement** les trois nouvelles adresses, et **aucune** des
  anciennes ;
- les **identifiants d'origine** ont survécu, comparés à
  `reference/etat-initial.tfstate` : `random_pet`, `random_integer` et
  `random_string` tirent des valeurs neuves à chaque création, donc une seule
  divergence signerait une recréation ;
- `plan -detailed-exitcode` rend **0** : code et state convergent ;
- le troisième déplacement a bien été fait **en déclaratif**. Le test le rejoue
  dans une copie : il ramène l'objet à son ancienne adresse, replanifie, et exige
  un `previous_address` porteur d'un `no-op`. Terraform n'écrit ce champ **que**
  si un bloc `moved` a été pris en compte, jamais après un `state mv` ;
- contrôle négatif : bloc `moved` retiré, le même plan repasse en `delete` plus
  `create`, ce qui est exactement le changement cassant décrit par la
  documentation.

Bloqué ? `dsoxlab hint state-terraform-state-mv`.
