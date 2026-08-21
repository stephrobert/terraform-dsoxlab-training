# 🎯 Challenge : la configuration qui refuse les valeurs absurdes

## ✅ Objectif

`challenge/work` contient un projet dont `variables.tf` et `main.tf` sont troués.
`terraform plan` échoue en l'état : les `???` ne sont pas du HCL valide.

Votre mission : calculer les valeurs par expression conditionnelle, puis
**placer chaque garde au bon niveau**. Le piège central est de croire que
`validation` suffit à tout.

## 📋 Ce qui est fourni

| Fichier | État |
|---|---|
| `versions.tf` | complet (`required_version = ">= 1.9.0"`) |
| `outputs.tf` | **complet, à ne pas modifier** |
| `variables.tf` | deux validations à écrire |
| `main.tf` | trois `locals`, un `content`, une `precondition`, une `postcondition`, un bloc `check` |

## 🎯 Les huit exigences

1. `environment` n'accepte que `dev`, `staging` ou `prod`.
2. `backup_bucket` est refusé **vide** quand `environment` vaut `prod`, accepté
   vide sinon. La condition référence donc une **autre** variable, ce
   qu'autorise Terraform 1.9.
3. `memory_mib` vaut 512 en `dev`, 2048 en `prod`, et cède la place à
   `memory_mib_override` dès qu'il n'est pas `null`. `vcpu` vaut 1, 2 ou 4.
4. `second_disk_name` vaut `null` quand le flag est faux, ce qui fait
   **disparaître** l'output, au lieu de l'exposer à `null`.
5. La `precondition` bloque dès que le rapport mémoire sur vCPU tombe sous
   **256 MiB**.
6. La `postcondition` relit `self.content` et exige un JSON portant une clé `env`.
7. Le bloc `check` est **en échec en `prod`, et c'est voulu** : l'`apply` doit
   réussir malgré lui.
8. Un second plan juste après l'apply ne propose plus rien.

## 🧩 Le cœur du sujet

Les quatre mécanismes ne sont pas interchangeables. Ils diffèrent par **le
moment** où ils s'évaluent et par **ce qu'ils bloquent** :

| Mécanisme | Peut porter sur | Effet en cas d'échec |
|---|---|---|
| `validation` | une **variable d'entrée** uniquement | arrête le plan |
| `precondition` | n'importe quelle expression, dont un `local` | arrête **avant** l'action |
| `postcondition` | le résultat réel, via `self` | arrête **après** l'action |
| bloc `check` | n'importe quelle expression | **avertit seulement** |

Deux conséquences directes pour ce lab :

- L'exigence 5 porte sur deux `locals`. **Aucun bloc `validation` ne peut la
  porter**, puisqu'une validation ne vit que sur une variable d'entrée.
- L'exigence 7 exige un mécanisme **non bloquant**. Une `precondition` ferait
  échouer l'apply, ce qui serait un échec du lab.

## 🔍 Validation

```bash
dsoxlab check write-code-conditionals
```

Les tests ne lisent jamais vos `.tf`. Ils lancent Terraform avec différentes
variables et n'exploitent que des **codes retour** et le tableau **`checks`** de
`terraform show -json`, dont le champ `kind` prouve quel mécanisme vous avez
réellement écrit.
