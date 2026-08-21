# Défi : faire parler le provider AWS à une API locale

`challenge/work` contient cinq fichiers. Deux sont troués, un troisième est
réduit au strict minimum.

| Fichier | État |
| --- | --- |
| `terraform.tf` | `source` et `version` du provider valent `???` |
| `providers.tf` | le bloc ne porte que `region` |
| `outputs.tf` | les trois `value` valent `???` |
| `variables.tf` | complet, ne rien y changer |
| `main.tf` | complet, ne rien y changer |

## Ce qu'il faut atteindre

1. Provider `hashicorp/aws` en **6.x**, sous une contrainte bornée des deux
   côtés.
2. Des identifiants statiques factices dans la configuration.
3. Les trois validations qui interrogeraient le vrai AWS désactivées.
4. `endpoints` redirigeant le service `ec2` vers `var.floci_endpoint`.
5. `var.common_tags` appliqués par `default_tags`, pas par la ressource.
6. L'instance atteint l'état `running`.
7. Les trois outputs rendent l'identifiant, l'état et l'IP privée.
8. Un plan relancé après l'apply n'annonce aucun changement.

## Deux pièges mesurés

- `terraform validate` **passe** sur un provider incomplètement configuré. Il ne
  prouve rien ici : c'est le `plan` qui échoue.
- Un tag posé sur la ressource et un tag de même nom posé par `default_tags` ne
  produisent **ni erreur ni avertissement** : la valeur de la ressource gagne en
  silence.

## Barème

100 points, moins le coût des indices demandés (10, 15 et 20).

```bash
dsoxlab check aws-provider-aws-first-ec2
```
