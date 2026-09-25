# 🎯 Challenge : produire un inventaire Ansible depuis le state

## Point de départ

`challenge/work` contient une configuration incomplète. **Aucun cloud, aucun
hyperviseur** : le parc est simulé par des ressources dont certains attributs ne
sont connus **qu'après création**, comme une adresse allouée par un
ordonnanceur.

C'est délibéré : une valeur devinable ne prouverait rien.

## ✅ Objectif

1. **Le type du parc**, en structure explicite. Jamais `any`.
2. **Les adresses**, calculées depuis le CIDR de base et l'index de chaque
   serveur, **par une fonction HCL**.
3. **La ressource** du provider `local` qui écrit `inventaire.json`, sérialisé
   **par une fonction**.
4. **L'output**, qui expose l'inventaire sous forme **structurée**.

## 🧭 Quatre choix qui séparent un pont fiable d'un pont qui tient debout

**Un type explicite refuse au plan.** `map(object({ role = string, index =
number }))` rejette une entrée sans `index` **avant tout appel de provider**.
Avec `any`, la même faute passe le plan et casse plus loin, sur un message qui
ne nomme ni la variable ni l'entrée fautive.

**Une adresse se calcule.** `cidrhost(var.cidr_de_base, serveur.index)` suit le
réseau. Recopiée à la main, elle est juste aujourd'hui et fausse au premier
changement, **sans que rien ne le signale**.

**`jsonencode` plutôt qu'une concaténation.** Une chaîne construite à la main
produit du JSON *presque* valide : une virgule en trop, un guillemet oublié dans
un nom, et Ansible rend une erreur de parsing qui ne dit pas où.

**Un fichier géré disparaît avec le parc.** Un inventaire qui survit à la
destruction pointe vers des machines qui n'existent plus. Ansible s'y
connectera, échouera, et le message parlera de réseau.

## 🔍 Validation

```bash
dsoxlab check first-infra-ansible
```

Sept tests. Les adresses ne sont pas comparées à une liste écrite dans le test :
elles sont **recalculées** depuis le CIDR, deux calculs indépendants valant
mieux qu'une constante. Et le fichier doit porter les identifiants **tirés à la
création** : les adresses se devinent, ceux-là non.
