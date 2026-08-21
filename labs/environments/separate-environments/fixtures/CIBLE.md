# Deux environnements, deux états, un seul module

`challenge/work` contient un module partagé et **deux** configurations racine,
`envs/dev` et `envs/prod`. Ce ne sont pas deux dossiers : ce sont deux
**racines**, donc deux `terraform init`, deux plans, et surtout deux **états**
indépendants.

## Ce que chaque environnement doit produire

| Environnement | `environnement` | `repliques` | État attendu |
| --- | --- | --- | --- |
| `envs/dev` | `dev` | **1** | `etats/dev.tfstate` |
| `envs/prod` | `prod` | **3** | `etats/prod.tfstate` |

Les deux appellent le **même** module, `modules/plaque`, par un chemin relatif.
Le dupliquer serait exactement l'anti-pattern que cette organisation évite.

## Le backend, et pourquoi il est vide

Le bloc `backend "local" {}` des deux racines est **identique**, et il ne porte
aucun argument. Ce n'est pas un oubli : un bloc `backend` ne peut référencer
**aucune valeur nommée**.

```text
Error: Variables not allowed

  on main.tf line 12, in terraform:
  12:     path = "../etats/${var.env}.tfstate"

Variables may not be used here.
```

La configuration **partielle** est la réponse officielle : le fichier reste le
même partout, et les arguments manquants sont fournis à l'**initialisation**.

```bash
terraform init -backend-config=<votre-fichier>.hcl
```

À vous d'écrire, dans chaque racine, le fichier qui porte le `path` attendu.

## Ce que cette séparation garantit

Un `terraform destroy` dans `envs/dev` ne peut **pas** toucher `envs/prod` : les
deux états sont distincts, et chaque racine ne connaît que le sien. C'est cette
propriété que la validation vérifie, en détruisant réellement dev dans une copie.

L'argument officiel va plus loin que le confort : « Workspaces are not appropriate
for system decomposition or deployments requiring **separate credentials and
access controls** », parce que « CLI workspaces within a working directory use the
**same backend** ». Deux répertoires, c'est deux backends, donc deux jeux de
droits possibles.
