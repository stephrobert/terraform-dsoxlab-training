# Scénario : le premier run distant, pour de vrai

**Sous-objectifs d'examen visés : 6a et 6b, en pratique plutôt qu'en théorie.**

**C'est le seul lab du catalogue qui demande un compte HCP Terraform.** Les sept autres
s'arrêtent juste avant l'authentification, et c'est ce qui les rend jouables partout.
Celui-ci franchit cette frontière, et il est optionnel pour cette raison. Le plan gratuit
suffit, et [`docs/hcp-token.fr.md`](../../../docs/hcp-token.fr.md) explique le jeton.

Une équipe apprend que ses prochains déploiements passeront par HCP Terraform. Personne n'en
a jamais vu un : la plateforme est une page dans un navigateur, et le lien entre cette page
et un `terraform apply` reste obscur.

## Capacité visée

Provisionner la plateforme elle-même avec Terraform (projet, workspace, réglages
d'exécution, une variable qui vit dans le workspace), puis rattacher une configuration à ce
workspace et faire exécuter un run sur l'infrastructure de HashiCorp plutôt que sur sa
machine.

## D'où part l'apprenant

`challenge/work` contient deux répertoires :

1. `plateforme/`, qui pilote HCP Terraform par le provider `tfe`. Quatre `???` à compléter,
   et un nom d'organisation à renseigner dans `organisation.auto.tfvars`.
2. `application/`, une configuration ordinaire à qui il manque son bloc `cloud`. Elle crée
   un `random_pet` : ce qui compte n'est pas la ressource, c'est **où elle est calculée**.

## L'état à atteindre

1. Un projet `formation-terraform` existe dans l'organisation.
2. Un workspace `premier-run-distant` existe **dans ce projet**, en mode d'exécution
   `remote` et sans auto-apply.
3. Une variable `message` existe dans le workspace, de catégorie `terraform`, marquée
   sensible.
4. `application/` est rattaché à ce workspace par un bloc `cloud` écrit en toutes lettres.
5. Un run a été **appliqué** sur ce workspace, et le state distant porte `preuve_du_run`.

## Les deux pièges, tous deux mesurés

**`execution_mode` sur `tfe_workspace` est déprécié.** Mesuré le 2026-09-25 avec le provider
0.81 :

```
Warning: Argument is deprecated
Use resource `tfe_workspace_settings` to modify the workspace execution settings.
This attribute will be removed in a future release of the provider.
```

Un avertissement n'arrête pas un apply, et c'est exactement ce qui le rend dangereux : la
configuration marche aujourd'hui et cassera à la prochaine version majeure du provider, sans
que personne n'ait rien changé.

**La sensibilité se propage à travers les fonctions.** Mesuré le même jour :
`sha256(var.message)` reste tenu pour sensible, et un output racine qui en dérive doit être
annoté, alors même qu'une empreinte ne permet pas de remonter au secret. Terraform ne
regarde pas ce que fait la fonction.

## Comment on le prouve

Les tests interrogent l'**API de HCP Terraform**, et non le state local. Un state local
dirait ce que l'apprenant a demandé, jamais ce que la plateforme a fait.

Le test central cherche un run à l'état `applied` sur le workspace créé : rien, en local, ne
peut le fabriquer. Un autre lit la version courante du state distant et ses sorties, qui
n'existent que parce que le run les a calculées là-bas.

Le teardown détruit tout ce que le lab a créé dans l'organisation. Laisser traîner un projet
et un workspace dans le compte de quelqu'un est pire que de lui demander de rejouer deux
`apply` de trente secondes, et un lab qui ne range pas derrière lui n'a pas sa place ici.
