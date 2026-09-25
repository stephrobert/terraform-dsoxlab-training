# 🎯 Challenge : établir ce que six équipes peuvent réellement faire

## 📦 Point de départ

`challenge/work` contient deux répertoires. **Aucun compte nécessaire.**

| Fichier | État |
| --- | --- |
| `acces/equipes.auto.tfvars.json` | **fourni**, six équipes décrites |
| `acces/variables.tf`, `acces/versions.tf` | **fournis** |
| `acces/acces.tf` | deux `???`, avec l'échelle et les équivalences fournies |
| `questionnaire/questionnaire.tf` | **fourni**, à ne pas modifier |
| `questionnaire/reponses.auto.tfvars` | cinq `???` à renseigner |

## ✅ Objectif

1. **Calculer l'accès effectif de chaque équipe** sur le workspace, à partir de
   ce qu'elle détient aux niveaux organisation, projet et workspace.
2. **Lister les équipes qui peuvent appliquer.** Appliquer demande au moins
   l'écriture.
3. **Répondre aux cinq questions.**

Écrivez une **règle**, pas une liste de réponses : aucune clé d'équipe ne doit
apparaître dans votre expression, et une septième équipe doit être traitée sans
rien réécrire.

## 🧭 Le piège, et c'est une habitude solide

Partout ailleurs, la permission posée au niveau le plus spécifique l'emporte.
Ici, les permissions **s'additionnent**, et l'accès effectif est le **plus
permissif** des trois niveaux, quel que soit celui qui l'a accordé.

Deux cas du fichier sont les exemples de la documentation elle-même, un dans
chaque sens. Si votre règle les rend justes tous les deux, c'est très
probablement la bonne.

Attention à l'autre sur-correction : rien ne s'accumule. Deux droits de lecture
ne font pas une écriture.

## ⚠️ Les deux échelles ne sont pas la même

| Portée | Rôles |
| --- | --- |
| workspace | `Read` < `Plan` < `Write` < `Admin` |
| projet | `Read` < `Write` < `Maintain` < `Admin` |

`plan` n'existe qu'au niveau workspace, `maintenance` qu'au niveau projet, et il
se place au-dessus de l'écriture. L'échelle fournie réunit déjà les deux :
servez-vous en plutôt que de comparer au jugé.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-projects-teams
```

Treize tests, tous lisant `terraform output -json` : ce que votre configuration
**calcule**, jamais ce qu'elle contient.

Bloqué ? `dsoxlab hint hcp-terraform-projects-teams`.
