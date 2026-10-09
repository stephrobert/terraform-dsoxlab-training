# Épreuve de niveau C : faire d'un copier-coller un module versionné

Deux équipes ont copié-collé la même configuration de machine libvirt, et les
deux copies ont divergé. `equipe-web/` est **en service** : ses deux machines
tournent. `equipe-data/` n'est pas encore déployée. L'adresse du dépôt Git où
publier le module, l'image de base et le préfixe sont dans `contexte.txt`.

Durée indicative : **2 heures**. Aucun indice n'est proposé.

## Le contrat du module

Une machine : un disque de 6 Gio en copie sur écriture de l'image de base, et
un domaine qui démarre, avec 1 vCPU, sur le réseau libvirt demandé.

| Version | Entrées | Ce qui change |
|---|---|---|
| `v1.0.0` | `nom`, `taille`, `image_de_base`, `reseau` | `taille` vaut `petite` (512 Mio) ou `moyenne` (768 Mio), toute autre valeur est refusée |
| `v1.1.0` | + `vcpu`, facultatif | le nombre de vCPU ; sans lui, rien ne change pour l'appelant |
| `v2.0.0` | `memoire_mib` **remplace** `taille` | la mémoire se donne en Mio : un appelant de la v1 doit s'adapter |

Le module est publié dans le dépôt, chaque version sous son tag. Il est
**testé** par `terraform test`, et ses tests couvrent le contrat : le harnais
abîmera le module (valeurs des tailles, refus d'une taille inconnue) et
s'attend à ce que vos tests le voient.

## Ce qui est attendu

Des résultats, vérifiés sur l'état réel, jamais sur la forme de votre code :

- **Le module se réutilise tel quel.** Il s'appelle en `for_each`, et il ne
  contraint que la version **minimale** du provider libvirt.
- **Le projet en service passe au module sans recréer ses machines.** Les
  machines de `equipe-web` gardent leur identité, et son plan ne propose plus
  rien.
- **Deux façons de consommer.** `equipe-data` est **figée au contenu** de la
  version 1.0.0 : rien de ce qu'on fera au dépôt ne pourra changer ce qu'elle
  obtient. Elle déploie ses deux machines, aux tailles de sa copie.
  `equipe-web` **suit les versions publiées** de la majeure 1 : elle obtient
  la 1.1.0 sans qu'on touche à son code, et n'obtiendra jamais la 2.0.0 par
  surprise.

## Comment c'est noté

Le rapport donne un verdict par compétence : `modularize`, `reuse`. Une
compétence en échec renvoie aux leçons qui l'enseignent.

Pour faire noter : `dsoxlab check`.
