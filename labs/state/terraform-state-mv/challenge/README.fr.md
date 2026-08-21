# 🎯 Challenge : rattacher trois objets existants, sans en détruire aucun

## ✅ Objectif

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

## 🔍 Validation

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
