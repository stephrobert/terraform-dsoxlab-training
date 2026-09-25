# 🎯 Challenge : jouer un run, puis en qualifier six autres

## 📦 Point de départ

`challenge/work` contient deux répertoires. **Aucun compte nécessaire** : la
moitié « run » se joue en local, avec les plans enregistrés.

| Fichier | État |
| --- | --- |
| `run/versions.tf`, `run/main.tf` | **fournis**, à ne pas modifier |
| `analyse/situations.auto.tfvars.json` | **fourni**, six runs décrits |
| `analyse/variables.tf`, `analyse/versions.tf` | **fournis** |
| `analyse/verdicts.tf` | un `???` : l'issue de chaque run |
| `analyse/etapes.tf` | un `???` : les onze étapes, dans l'ordre |
| `analyse/faits.tf` | trois `???` : des faits à établir |

## ✅ Objectif

1. **Jouer un premier run** dans `run/` : enregistrer son plan dans
   `run1.tfplan` avec le message `premier-run`, puis appliquer **ce plan**.
2. **Planifier un second run** dans `run2.tfplan` avec le message `second-run`,
   et le **laisser en attente**. C'est un run arrêté en « Needs Confirmation » :
   planifié, pas appliqué.
3. **Conserver les deux fichiers de plan.** Ce sont eux qui prouvent le travail.
4. **Qualifier les six runs**, avec cinq mots et pas un de plus :
   `plan_speculatif`, `planned_and_finished`, `apply_automatique`,
   `attend_confirmation`, `aucun_run_distant`.
5. **Ordonner les onze étapes**, et **établir trois faits**.

## 🧭 Essayez ce qui est refusé

Une fois le premier run appliqué, essayez de rejouer son plan. Et essayez de
passer un `-var` à l'apply du second. Les deux sont refusés, et chacun de ces
refus a un pendant dans HCP Terraform : la file de runs d'un workspace, et un run
verrouillé sur son jeu de variables.

Ces deux messages d'erreur méritent d'être lus en entier. Ils disent davantage de
ce qu'est un run que n'importe quelle définition.

## ⚠️ Aucune réponse constante ne passe

| Réponse uniforme | Échoue sur |
| --- | --- |
| `attend_confirmation` partout | les quatre autres cas |
| `apply_automatique` partout | cinq des six |
| `plan_speculatif` partout | cinq des six |

Deux pièges en particulier : le réglage d'auto-apply ne fait rien appliquer à une
pull request, et il n'applique pas un plan qui ne porte aucun changement.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-hcp-terraform-overview
```

Quinze tests. La moitié « run » lit le disque et les plans enregistrés par
`terraform show -json` ; le reste lit `terraform output -json`, donc ce que votre
configuration **calcule**, jamais ce qu'elle contient.

Bloqué ? `dsoxlab hint hcp-terraform-hcp-terraform-overview`.
