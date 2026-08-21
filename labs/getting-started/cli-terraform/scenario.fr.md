# Scénario : la CLI Terraform comme outil d'automatisation

**Sous-objectif d'examen visé : 3c, exécuter le workflow Terraform en automation.**

Un lab qui vérifierait que des commandes ont été tapées ne prouverait rien. Ce
qui se prouve, c'est qu'une chaîne non interactive traverse la configuration
sans qu'un humain n'ait à lire une seule sortie formatée pour lui.

## Capacité visée

Piloter Terraform depuis un script : obtenir un verdict par code retour,
exploiter les sorties machine (`-json`) plutôt que le texte affiché, et évaluer
une expression HCL sans ouvrir de session interactive.

## D'où part l'apprenant

`challenge/work` contient une configuration reposant uniquement sur les
providers `local`, `null` et `random` : aucun cloud, aucune VM, aucun coût. Le
répertoire est vierge, sans `.terraform/`, sans fichier de verrouillage, sans
state.

Trois défauts sont posés volontairement : un fichier `.tf` hors format canonique
qui fait sortir `terraform fmt -check` en code non nul, une erreur qui fait
échouer `terraform validate` (`valid` à `false`, `error_count` supérieur à
zéro), et des outputs manquants alors qu'ils sont le seul canal par lequel la
configuration expose ses valeurs à un script. Tout doit tourner sans
confirmation interactive.

## L'état à atteindre

1. Le répertoire est initialisé et le fichier de verrouillage existe. Sans cette
   étape, `validate` échoue pour une raison étrangère à la qualité du code.
2. Plus aucun fichier n'est hors format canonique.
3. La configuration est valide, sans diagnostic de sévérité `error`.
4. La configuration est appliquée sans interaction, et le state contient
   exactement les adresses de ressources attendues.
5. Les outputs demandés existent et portent les valeurs calculées par la
   configuration, dont une valeur issue d'une expression que l'on doit pouvoir
   recalculer hors du state.
6. Rejouer un plan après l'apply n'annonce aucun changement.

## Comment on le prouve

Aucun test ne relit le `.tf` de l'apprenant, aucun ne parse une sortie humaine.
Tout passe par des codes retour et du JSON :

- `terraform fmt -check -recursive` doit sortir en 0. Un code non nul prouve
  qu'un fichier reste hors format canonique : c'est le contrat annoncé par la
  documentation officielle.
- `terraform validate -json` est parsé : `valid` vaut `true` et `error_count`
  vaut `0`.
- `terraform output -json` est parsé : les clés attendues sont présentes et
  leurs valeurs correspondent à ce que la configuration doit produire.
- `terraform state list` liste exactement les adresses attendues, et
  `terraform show -json` confirme leur présence dans le state.
- Une expression est évaluée en mode non interactif, en la passant sur l'entrée
  standard de `terraform console`, et le résultat est comparé à la valeur
  attendue.
- `terraform plan -detailed-exitcode` sort en 0, soit succès sans changement. Un
  2 signalerait une dérive, un 1 une erreur.
