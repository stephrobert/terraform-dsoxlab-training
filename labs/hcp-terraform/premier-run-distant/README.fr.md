# Provisionner la plateforme, puis la laisser exécuter votre infrastructure

**C'est le seul lab du catalogue qui demande un compte HCP Terraform.** Les sept
autres s'arrêtent volontairement juste avant l'authentification, et c'est ce qui
les rend jouables partout. Celui-ci franchit cette frontière, et il est optionnel
pour cette raison.

Le plan gratuit suffit.
[`docs/hcp-token.fr.md`](../../../docs/hcp-token.fr.md) explique comment créer le
jeton et où le poser :

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

## Terraform provisionne Terraform

Le provider `tfe` pilote HCP Terraform lui-même : organisations, projets,
workspaces, variables, équipes. C'est l'infrastructure as code appliquée à la
plateforme qui exécute votre infrastructure as code, et le saut mental vaut d'être
fait une fois.

```hcl
resource "tfe_workspace" "demo" {
  organization = data.tfe_organization.courante.name
  name         = var.workspace
  project_id   = tfe_project.formation.id
}
```

Sans `project_id`, le workspace atterrit dans le projet par défaut de
l'organisation, et rien ne vous le dit.

## Les réglages ont déménagé, et l'avertissement ne vous arrête pas

Mesuré le 2026-09-25 avec le provider 0.81 :

```
Warning: Argument is deprecated

  with tfe_workspace.essai,
  on main.tf line 30, in resource "tfe_workspace" "essai":
  30:   execution_mode = "remote"

Use resource `tfe_workspace_settings` to modify the workspace execution
settings. This attribute will be removed in a future release of the provider.
```

Un avertissement n'arrête pas un apply, et c'est précisément ce qui le rend
dangereux : la configuration marche aujourd'hui et cassera à la prochaine version
majeure du provider, sans que personne n'ait rien changé. Les réglages
d'exécution vivent donc dans leur propre ressource :

```hcl
resource "tfe_workspace_settings" "demo" {
  workspace_id   = tfe_workspace.demo.id
  execution_mode = "remote"
  auto_apply     = false
}
```

## Ce que `remote` change vraiment

Avec `execution_mode = "remote"`, `terraform apply` ne calcule plus rien sur
votre machine. Il envoie une archive du répertoire, HCP Terraform exécute le plan
sur une VM jetable, vous renvoie les journaux au fil de l'eau, et conserve le
state.

Mesuré le 2026-09-25 : un run distant complet prend **une trentaine de secondes**
sur le plan gratuit, envoi et destruction de la VM compris.

Deux conséquences en découlent, et ce lab vous les fait constater :

- la variable `message` est déclarée dans la configuration **sans valeur**. C'est
  le workspace qui la fournit au moment du run. Lancez le répertoire sans
  rattachement, Terraform vous la demande ; rattaché, il ne demande rien ;
- le state ne touche jamais votre disque. `terraform output` le relit par le
  réseau.

## La sensibilité voyage plus loin qu'on ne croit

Mesuré le même jour, et cela m'a surpris :

```
Error: Output refers to sensitive values
  on main.tf line 34:
  34: output "empreinte_du_message" {
```

L'output valait `sha256(var.message)`, une empreinte, qu'on ne peut pas inverser.
Terraform ne regarde pas ce que fait la fonction : **tout ce qui dérive d'une
valeur sensible est sensible**, et un output racine qui en dérive doit être
annoté. Notez que cela vaut pour les outputs racine ; la même expression dans un
attribut de ressource passe, comme le montre le lab `shared-credentials`.

## À vous

```bash
dsoxlab run hcp-terraform-premier-run-distant
dsoxlab check hcp-terraform-premier-run-distant
dsoxlab hint hcp-terraform-premier-run-distant
```

Neuf tests, tous lisant l'**API de HCP Terraform** : un state local dirait ce que
vous avez demandé, jamais ce que la plateforme a fait. Le test central cherche un
run à l'état `applied`, que rien en local ne peut fabriquer.

**Le check range derrière lui** : il détruit le projet et le workspace qu'il a
créés. Les laisser dans votre compte serait pire que de rejouer deux `apply` de
trente secondes.

Sous-objectifs d'examen visés : **6a** et **6b**, en pratique.

Référence : [le workflow de run par la CLI](https://developer.hashicorp.com/terraform/cloud-docs/run/cli)
