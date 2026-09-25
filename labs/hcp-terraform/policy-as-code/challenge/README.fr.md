# 🎯 Challenge : qui bloque un run, et qui peut passer outre

## 📦 Le point de départ

`challenge/work` contient une configuration **sans aucun provider** : ce lab ne
crée rien, il raisonne et il lit.

| Fichier | État |
| --- | --- |
| `situations.auto.tfvars.json` | **fourni**, sept runs décrits |
| `variables.tf`, `versions.tf` | **fournis** |
| `verdicts.tf` | un `???` : le verdict de chaque run |
| `connaissances.tf` | trois `???` : des faits à établir |
| `evaluation.tf` | un `???` : la règle de conformité |
| `plans/` | deux **vraies** sorties de `terraform show -json` |

## ✅ Objectif

1. **Qualifier les sept runs**, avec trois valeurs et pas une de plus :
   `poursuit`, `bloque_surchargeable`, `bloque`.
2. **Établir trois faits** : les niveaux de chaque framework, ce qui distingue
   les policy checks des evaluations, et ce que l'édition Free autorise.
3. **Écrire la règle de conformité** : aucun fichier créé avec un droit accordé
   au reste du monde. Elle rend les **adresses** fautives, pas un booléen.

## 🧭 Le piège, et il fait tomber les candidats

Un `hard-mandatory` **n'est pas indépassable**. Ce qui décide de l'override est
le **réglage du policy set**, croisé avec la **permission** de l'utilisateur :

> Override capability is controlled by the policy set setting, not individual
> enforcement levels.

Le niveau ne décide que d'une chose : un `advisory` ne bloque jamais. Pour tout
le reste, il faut **les deux** : que le policy set l'autorise, et que
l'utilisateur détienne *Manage Policy Overrides*.

Chaque situation porte ces trois informations. Servez-vous en.

## ⚠️ Aucune réponse constante ne passe

Les sept cas sont bâtis pour cela :

| Réponse uniforme | Échoue sur |
| --- | --- |
| `bloque` partout | les deux cas `advisory` |
| `bloque_surchargeable` partout | les trois cas sans droit |
| `poursuit` partout | les cinq autres |

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-policy-as-code
```

Treize tests, tous lus dans `terraform output -json` : ce que votre
configuration **calcule**, jamais ce qu'elle contient.

Les sept cas sont assérés un par un, pour que le message dise lequel est faux.
Et la règle de conformité est éprouvée dans les **deux sens** : une règle qui
refuse tout échoue sur le plan conforme.

Bloqué ? `dsoxlab hint hcp-terraform-policy-as-code`.
