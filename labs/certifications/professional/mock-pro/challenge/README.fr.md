# Pro, examen blanc intégratif

## La situation

**Objectifs d'examen visés : les six**, dans les conditions de l'épreuve réelle.

L'examen Terraform Authoring and Operations Professional dure **quatre heures**
et mêle QCM et travaux pratiques : écrire du code, diagnostiquer, réparer. La
documentation Terraform et celle des providers sont accessibles pendant
l'épreuve.

## Capacité visée

Enchaîner, dans le temps imparti et sans aide, six tâches couvrant les six
objectifs. Ce n'est pas un lab d'apprentissage : c'est une répétition générale,
à jouer une fois les six capstones réussis, et d'une traite.

## D'où part l'apprenant

`challenge/work` contient six répertoires, un par tâche, chacun volontairement
imparfait. Des fichiers déjà posés hors Terraform, une configuration qui ne
valide pas, trois copies d'un même couple de ressources, deux racines qui
s'ignorent, une configuration de provider absente, et douze questions sans
réponse.

Le lab se joue **hors ligne**, avec les providers `local` et `random` : aucune
VM, aucun compte, aucun émulateur. C'est un choix, et il a un prix, dit plus bas.

## L'état à atteindre

1. **Objectif 1** : adopter un fichier corrigé à la main sans écraser sa
   correction, et obtenir un plan stable.
2. **Objectif 2** : réparer trois fautes que `validate` nomme, remplacer trois
   ressources par une seule portée par `for_each`, et faire refuser au plan un
   port hors de la plage autorisée.
3. **Objectif 3** : exposer un contrat en sorties depuis une racine, le
   consommer depuis l'autre, sans rien recopier en dur.
4. **Objectif 4** : factoriser trois environnements dans un module local, sans
   qu'aucune ressource soit détruite ni recréée.
5. **Objectif 5** : rattacher explicitement une ressource à une seconde
   configuration du provider, poser les droits au bon endroit, et écrire une
   contrainte de version qui encadre la série.
6. **Objectif 6** : répondre aux douze questions HCP Terraform, avec un seuil
   global et une couverture des quatre sous-objectifs.

## Comment on le prouve

- **Une section de tests par tâche**, indépendante des autres : une tâche ratée
  ne fait pas échouer les suivantes, et le score dit quel objectif retravailler.
- Les preuves se lisent dans l'état : `terraform show -json`, le state, le
  fichier de verrouillage, les droits réels sur le disque.
- Trois tâches exigent un plan **stable** après travail, ce qui interdit de
  réussir par un détour qui reconstruit à chaque passage.

## Ce que ce mock ne couvre pas, et pourquoi

Les providers locaux ne savent pas importer : `local` comme `null` répondent
`Resource Import Not Implemented`. L'import est donc éprouvé ailleurs, par
`capstone1-resource-lifecycle` et `aws-import-moved-drift`, qui ont un vrai
provider. Ici, la tâche 1 éprouve l'autre moitié du même sous-objectif, la
réconciliation d'une dérive.

Pour la même raison, l'objectif 5 est éprouvé sur le rattachement et la
contrainte de version, non sur l'authentification d'un provider distant.

## 🎯 Challenge : Pro, examen blanc intégratif

### 📦 Le point de départ

`challenge/work` contient **six répertoires**, un par objectif. Chacun porte ses
consignes en commentaire, en tête de `main.tf`, et chaque `???` marque ce qui
reste à écrire.

| Répertoire | Ce qu'il contient |
| --- | --- |
| `t1-derive/` | un `existant.txt` posé hors Terraform, et une configuration à écrire autour |
| `t2-dynamique/` | une configuration qui **ne valide pas**, et trois ressources jumelles |
| `t3-etats/` | deux racines, `socle/` et `app/`, qui s'ignorent encore |
| `t4-module/` | trois environnements écrits trois fois, déjà appliqués |
| `t5-providers/` | une seule configuration de provider, là où il en faut deux |
| `t6-hcp/` | `questions.fr.md` (douze questions), `reponses.auto.tfvars` à remplir, `bareme.tf` et `versions.tf` **fournis, à ne pas modifier** |

L'ordre est libre : chaque tâche est notée indépendamment des autres. Traitez
d'abord celles que vous savez faire, l'examen se joue aussi comme cela.

### ✅ Ce qu'il faut obtenir

#### `t1-derive/` , objectif 1

1. `local_file.inventaire` gère `existant.txt`, et **son contenu est inchangé**.
2. `terraform plan -detailed-exitcode` rend **0** après l'apply.

#### `t2-dynamique/` , objectif 2

3. Les trois fautes sont corrigées : `terraform validate` passe.
4. Les trois fichiers viennent d'**une seule** ressource, portée par `for_each`.
5. Chaque fichier porte son port, et la variable **refuse au plan** un port hors
   de 1024-65535.

#### `t3-etats/` , objectif 3

6. Le socle expose son identifiant et sa zone en sorties.
7. L'application les lit par une source de données, **sans rien recopier**.
8. Rejouer le socle avec une autre zone fait suivre l'application.

#### `t4-module/` , objectif 4

9. Les trois environnements passent par un module local.
10. **Aucune ressource n'est recréée** : les identifiants du state sont les
    mêmes qu'avant, et le plan est stable.

#### `t5-providers/` , objectif 5

11. Une seconde configuration du provider, **aliasée**, rend `prive/`.
12. `prive/` est en 700 et `prive/note.txt` en 600 ; `public/` garde le défaut.
13. La contrainte du provider accepte la série 2 à partir de la 2.5 et refuse
    la 3.0.

#### `t6-hcp/` , objectif 6

14. Les **douze** réponses dans `reponses.auto.tfvars`, plus aucun `???`.
15. **Score global d'au moins 75 %**, et **aucun sous-objectif sous 50 %**.

### 🧭 Le format des réponses

| Type | Ce qu'on attend | Exemple |
| --- | --- | --- |
| choix unique | une lettre | `b` |
| choix multiple | les lettres **triées**, collées | `ac`, jamais `ca` |

La casse et les espaces autour sont ignorés. Une entrée laissée à `???` compte
comme une absence, et les tests exigent qu'il n'en reste aucune.

```bash
cd t6-hcp
terraform output corrige                   # quelles questions sont fausses
terraform output score_par_sous_objectif   # quel sous-objectif est faible
terraform output sans_reponse              # ce qui reste à remplir
```

### ⚠️ Trois pièges, et ils ont tous été mesurés

**Le contenu de `existant.txt`.** Le décrire approximativement donne un state
juste, un plan stable, et un fichier réécrit : la correction posée à la main est
perdue. Reprenez le contenu **exactement**, retour à la ligne final compris.

**Les droits, dans la tâche 5.** Le provider `local` n'accepte aucun argument.
`directory_permission` dans un bloc `provider` fait échouer l'apply sur
`An argument named "directory_permission" is not expected here.` Les droits se
posent sur la ressource, et ils y sont deux.

**Le barème, dans la tâche 6.** Il ne porte que des empreintes `sha256` salées.
Les remplacer par celles de ses propres réponses donne 100, et le test le
refuse : il vérifie d'abord que les douze empreintes sont intactes.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-mock-pro
```

Seize tests, groupés par tâche. Ils lisent `terraform show -json`, le state, le
fichier de verrouillage et les droits réels sur le disque, jamais vos `.tf`.
Trois tâches exigent un plan stable : une solution qui reconstruit à chaque
passage échoue, même si le fichier produit est bon.

Bloqué ? `dsoxlab hint certifications-professional-mock-pro`.
