# 🎯 Challenge : une chaîne qui tourne sans personne pour la lire

## Point de départ

`challenge/work` contient une configuration reposant sur `local`, `null` et
`random` : aucun cloud, aucune VM, aucun coût. Le répertoire est vierge, sans
`.terraform/`, sans verrou, sans state.

**Trois défauts sont posés volontairement** dans `main.tf`, et son en-tête les
annonce :

1. le fichier n'est **pas au format canonique** ;
2. il référence une variable qui n'est **déclarée nulle part** ;
3. **aucun output** n'expose les valeurs calculées.

## ✅ Objectif

Corrigez les trois, **sans changer ce que la configuration produit**, puis
menez la chaîne complète sans une seule confirmation interactive.

1. `terraform init` réussi, verrou présent.
2. Plus aucun fichier hors format.
3. `validate` sans diagnostic de sévérité `error`.
4. La configuration appliquée, le state portant exactement
   `random_pet.nom`, `local_file.rapport` et `null_resource.marqueur`.
5. Trois outputs : `nom_animal`, `chemin_rapport` et `nom_majuscule`. Le
   dernier est une **expression**, pas une recopie.
6. Un plan rejoué après l'apply n'annonce rien.

## 🧭 L'ordre compte, et la première étape surprend

**`validate` a besoin des schémas des providers.** Lancé avant `init`, il échoue
pour une raison qui n'a rien à voir avec la qualité de votre code. Initialisez
d'abord, sinon vous corrigerez une erreur qui n'existe pas.

**`fmt` ne se corrige pas à la main.** `terraform fmt -recursive` fait le travail,
et `-check` sert à vérifier, pas à réparer.

**Un output est le seul canal officiel vers un script.** Une valeur qui n'y
figure pas n'est pas accessible de l'extérieur, sauf à fouiller le state, ce qui
revient à dépendre d'un format interne.

## 🔍 Validation

```bash
dsoxlab check getting-started-cli-terraform
```

Aucun test ne relit votre `.tf`, aucun ne parse une sortie destinée à un humain.
Tout passe par des codes retour et du JSON : `validate -json` pour `valid` et
`error_count`, `output -json` pour les valeurs, `show -json` pour le state.

Une expression est évaluée **hors session interactive**, en la passant sur
l'entrée standard de `terraform console`, et son résultat est comparé à la
valeur attendue : c'est ainsi qu'on prouve un calcul sans lire le code qui le
fait.

Et `plan -detailed-exitcode` doit sortir en **0**. Un 2 signalerait une dérive,
un 1 une erreur : sans ce drapeau, les trois cas se ressemblent.

Bloqué ? `dsoxlab hint getting-started-cli-terraform`.
