# 🎯 Challenge : deux stacks qui se parlent

## 📦 Le point de départ

Un monorepo **déjà découpé** mais **non branché**. Rien n'est initialisé, aucun
état n'existe.

| Chemin | Ce que c'est |
| --- | --- |
| `modules/reseau/` | module local **complet**, à ne pas modifier |
| `stacks/plateforme/` | appelle le module, `outputs.tf` **vide**, un secret déclaré |
| `stacks/applicatif/` | consomme la plateforme, bloc `data` **troué** |
| `CIBLE.md` | l'état à atteindre et les trois faits qui décident |

## ✅ Ce qu'il faut obtenir

1. `stacks/plateforme` s'initialise.
2. Son état contient les ressources du module, dont `random_password.db`.
3. Ses sorties racine exposent `network_name` et `network_cidr`.
4. **Aucune** sortie racine ne porte le mot de passe.
5. `stacks/applicatif` a une entrée `mode: data` de type
   `terraform_remote_state`.
6. Son `network_cidr` vaut **exactement** celui de la plateforme, et le fichier
   qu'elle produit le contient.
7. Les deux stacks sont **idempotentes**.

## ⚠️ Le cœur du sujet

Trois faits, chacun mesuré, décident de tout le travail.

**Un module local n'accepte pas `version`.** L'`init` échoue, et le message dit
exactement pourquoi. Lisez-le avant de supprimer la ligne.

**Seules les sorties de la RACINE traversent.** Une sortie de module imbriqué
reste invisible depuis une autre configuration : ce qui doit franchir la
frontière se ré-exporte explicitement.

**Publier une sortie, c'est publier tout l'état.** « any user or server which has
enough access to read the root module output values will also always have access
to the full state snapshot data ». Le mot de passe n'a donc rien à faire dans une
sortie racine, même marqué `sensitive`.

## 🔍 Validation

`dsoxlab check environments-monorepo-vs-repo-per-stack` prouve, par exécution :

- que la plateforme suit bien le module **et** son secret ;
- qu'elle **ré-exporte** ses deux sorties à la racine ;
- qu'**aucune** de ses sorties ne porte le mot de passe, comparé **valeur par
  valeur** et non sur le texte brut ;
- que l'applicatif lit réellement l'**état** amont ;
- que le CIDR est **identique** des deux côtés. Il est tiré au sort à l'apply :
  le recopier ne tiendra pas ;
- que les deux stacks ont convergé.

Bloqué ? `dsoxlab hint environments-monorepo-vs-repo-per-stack`.
