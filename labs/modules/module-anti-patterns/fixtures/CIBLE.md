# Ce qu'il faut refactorer, et ce qu'il est interdit de casser

`projet/` est **déjà appliqué** : son state contient deux `local_file` et leurs
deux `random_pet`, déclarés en vrac à la racine. C'est le point de départ le plus
courant en vrai, et le plus délicat à reprendre.

## Les trois défauts à corriger

| Défaut | Ce qu'il coûte |
| --- | --- |
| deux ressources **copiées-collées** à la racine, avec leurs valeurs figées | rien n'est réutilisable, et le troisième cas se fera par un troisième copier-coller |
| aucune **abstraction** : le projet manipule des fichiers, pas des plaques | le jour où une plaque devient autre chose, tout le projet change |
| l'interface, quand elle existera, sera **non typée** | une erreur d'appel ne se voit qu'au plan, ou pas du tout |

## L'état à atteindre

1. Un module `bibliotheque/plaque/` porte la ressource, **une seule fois**.
2. Le projet l'appelle **deux fois** depuis un **seul** bloc, pour `nord` et
   `sud`.
3. L'entrée du module est **typée** par un objet, pas laissée en `any` : elle
   porte au moins l'étiquette et le contenu.
4. La sortie `chemins` du projet garde **exactement** la même forme qu'aujourd'hui.

## L'interdit

**Rien ne doit être détruit ni recréé.** Les deux fichiers existent, ils sont dans
le state, et un refactoring qui les remplace n'est pas un refactoring : c'est une
panne. Déplacer une ressource change son **adresse**, et Terraform ne le devine
pas. Il existe un bloc, prévu exactement pour cela, qui lui dit qu'une adresse en
remplace une autre.

Le contrôle est simple : après votre travail, `terraform plan` ne doit annoncer
**aucun** changement, et les identifiants du state doivent être **les mêmes**
qu'au départ :

```bash
terraform output jetons
```

```text
{
  "nord" = "becoming-gull"
  "sud"  = "stirring-porpoise"
}
```

Ces deux jetons sont tirés par un `random_pet`. Ils ne se **recalculent** pas :
détruire la ressource, c'est en obtenir deux autres. C'est exactement ce qui rend
le contrôle honnête.

## Un détail qui compte

Le bloc de déplacement ne sert **qu'aux changements d'adresse**. Il ne transforme
pas une ressource gérée en source de données, il ne corrige pas une variable non
typée, et il ne déplace pas une configuration de provider. Chaque défaut a sa
propre correction.
