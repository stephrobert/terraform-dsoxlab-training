# Quand plusieurs règles s'appliquent en même temps

L'objectif 6 du Professional est évalué **en QCM**, et ce capstone ne demande
**aucun compte**. Il ne rejoue pas les sept labs de la section : il les croise.

C'est la différence entre connaître une règle et savoir laquelle l'emporte.

## Trois questions qui se répondent dans l'ordre

Pour qualifier un run, les règles ne commutent pas. Chacune rend la suivante
sans objet :

| Question | Si oui |
| --- | --- |
| le workspace exécute-t-il quelque chose ? | sinon, rien d'autre ne compte |
| ce run pourra-t-il appliquer, un jour ? | sinon, aucune policy n'a d'objet |
| y a-t-il quelque chose à appliquer ? | sinon, le run se termine |
| une policy s'y oppose-t-elle ? | et peut-on passer outre ? |
| l'apply part-il tout seul ? | réglage **et** déclencheur |

## Les trois pièges, et pourquoi ils se ressemblent

Ils ont tous la même forme : une règle vraie, appliquée à une question qui ne se
pose pas.

**Une policy `mandatory` en échec sur une pull request ne bloque rien.** La
règle « mandatory bloque » est juste. Elle ne s'applique pas ici, parce qu'un
plan spéculatif ne peut pas appliquer : il n'y a rien à bloquer.

**Un `advisory` en échec n'empêche pas un auto-apply.** La règle « une policy en
échec arrête le run » est fausse pour ce niveau, et c'est la seule chose que le
niveau décide.

**En mode d'exécution `local`, la question des policies ne se pose pas.** Le
workspace n'est plus qu'un stockage d'état : rien ne s'exécute chez HCP
Terraform, donc rien n'y est évalué.

## Ce que le capstone vous fait aussi écrire

**Un rattachement** (6b), en toutes lettres : un bloc `cloud` est résolu avant
toute évaluation d'expression, il n'accepte donc aucune valeur nommée. Une
configuration correcte va jusqu'à `Required token could not be found`, et c'est
la frontière du capstone.

**Une fiche sans secret** (6c). Deux mesures de la section s'y rejoignent :
`sensitive` protège l'affichage et laisse la valeur en clair dans le state, et
la sensibilité se propage à travers les fonctions, sans que Terraform regarde ce
qu'elles font. Une empreinte reste donc tenue pour sensible, et l'output qui la
publie doit être annoté.

## À vous

```bash
dsoxlab run   certifications-professional-capstone6-hcp
dsoxlab check certifications-professional-capstone6-hcp
dsoxlab hint  certifications-professional-capstone6-hcp
```

Huit tests. L'un d'eux vérifie que **les six verdicts sont tous différents** :
deux situations qui recevraient la même issue signaleraient une règle qui les
confond.

Objectif d'examen visé : **6**, en entier.

Référence : [Exercices Professional](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/professional/exercices/)
