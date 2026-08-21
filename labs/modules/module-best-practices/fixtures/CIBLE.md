# Ce que le module doit devenir

Le module `bibliotheque/plaque/` fonctionne, et c'est bien le probleme : il est
**inutilisable ailleurs**. Trois pratiques manquent, chacune verifiable dans les
artefacts que Terraform produit.

## 1. Un module ne configure pas son provider

Un bloc `provider` dans un module rend l'ensemble **indestructible proprement** :
« A provider configuration must always stay present in the overall Terraform
configuration for longer than all of the resources it manages ». Terraform le
sanctionne aussi a l'appel :

```text
Error: Module is incompatible with count, for_each, and depends_on
```

Le module doit **declarer** qu'il attend une configuration, et l'appelant doit la
lui **passer**. Deux mots-cles seulement : l'un se declare dans le
`required_providers` du module, l'autre est un meta-argument du bloc `module`.

## 2. Un module recoit ses dependances, il ne les fabrique pas

Le repertoire de sortie est decide **dans** le module. Il doit devenir une
**entree**, pour que l'appelant puisse brancher le module ou il veut. C'est
l'inversion de dependance, coeur de la page officielle sur la composition.

## 3. Un module se documente

La *Standard Module Structure* place le `README.md` dans le **minimum** :
« The root module and any nested modules should have README files ». C'est ce
fichier que le registre et les generateurs de documentation exploitent.

## Ce que le projet doit obtenir

| Attendu | Ou cela se lit |
| --- | --- |
| deux plaques, `nord` et `sud`, depuis **un seul** appel | le state |
| un repertoire de sortie choisi par le **projet**, `sorties` | le state |
| aucune configuration de provider declaree dans le module | le JSON du plan |
| une configuration **aliasee** passee par l'appelant | le JSON du plan |

Le projet declare deja sa sortie `chemins` sous forme de map : elle suppose donc
un appel **multiple**.
