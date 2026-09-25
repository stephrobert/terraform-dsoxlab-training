# 🎯 Challenge : faire tourner un run chez HashiCorp

## ⚠️ Le seul lab qui demande un compte

Les sept autres labs `hcp-terraform` se jouent sans rien. Celui-ci a besoin d'un
compte HCP Terraform, le plan gratuit suffit, et d'un jeton d'API posé sur votre
poste :

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

Sans jeton, les tests **skippent** : vous ne verrez pas de rouge, vous verrez où
trouver ce qui manque. Le guide est [`docs/hcp-token.fr.md`](../../../../docs/hcp-token.fr.md).

## 📦 Point de départ

| Fichier | État |
| --- | --- |
| `plateforme/organisation.auto.tfvars` | un `???` : **votre** organisation |
| `plateforme/plateforme.tf` | quatre `???` |
| `plateforme/versions.tf`, `variables.tf` | **fournis** |
| `application/versions.tf` | le bloc `cloud` manque |
| `application/main.tf` | **fourni**, à ne pas modifier |

## ✅ Objectif

1. **Renseigner votre organisation**, celle qui figure dans l'URL
   `app.terraform.io/app/<ici>`.
2. **Compléter `plateforme/`** : un workspace dans le projet, des réglages
   d'exécution, une variable sensible. Puis appliquer.
3. **Rattacher `application/`** au workspace créé, et lancer l'apply. C'est là
   que le run part chez HCP Terraform.

```bash
cd plateforme && terraform init && terraform apply
cd ../application && terraform init && terraform apply
```

## 🧭 Deux pièges, et le provider vous prévient pour l'un des deux

**`execution_mode` sur `tfe_workspace` est déprécié.** Le provider l'annonce,
l'apply réussit quand même, et la configuration cassera à la prochaine version
majeure. Les réglages d'exécution ont leur propre ressource.

**Le bloc `cloud` n'accepte aucune variable.** Vous le savez déjà : le lab
`hcp-workspaces` l'a établi, et il faut ici le réinvestir. Les valeurs à employer
sont celles que `terraform output` vous rend dans `plateforme/`.

## 🔎 Ce que vous devriez regarder pendant que ça tourne

L'apply de `application/` affiche une URL. Ouvrez-la : vous verrez le run que
vous venez de déclencher, ses journaux, son plan, et le bouton qui aurait servi
si vous aviez confirmé depuis l'interface plutôt que depuis la CLI.

## 🧹 Le check range derrière lui

`dsoxlab check` détruit le projet et le workspace créés. Pour revalider, rejouez
les deux `apply` : ils prennent une trentaine de secondes chacun.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-premier-run-distant
```

Neuf tests, tous lisant l'**API de HCP Terraform**. Le test central cherche un
run à l'état `applied` : un `terraform apply` joué en local, sans rattachement,
n'y laisse aucune trace.

Bloqué ? `dsoxlab hint hcp-terraform-premier-run-distant`.
