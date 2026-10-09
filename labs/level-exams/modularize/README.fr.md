# Épreuve de niveau C : modulariser

Cette épreuve clôt le niveau C de la formation Terraform. Ce n'est pas un
cours : elle mesure, sur un scénario neuf, deux compétences travaillées dans
le module Modules.

| Compétence | Ce qui est vérifié |
| --- | --- |
| `modularize` | trois versions publiées ; module appelable en `for_each`, plancher de version seul ; `terraform test` passe, et voit les régressions injectées ; le projet en service migre sans recréer ses machines |
| `reuse` | une équipe figée au contenu (SHA-1), qu'un tag déplacé ne touche pas ; l'autre suit les versions de la majeure 1 ; la 2.0.0 exige d'adapter l'appelant |

Prérequis du poste : Terraform 1.16, Git et libvirt (`qemu:///system`), comme
pour les labs de Premières infras. La préparation télécharge l'image cloud la
première fois, empreinte vérifiée.

Cette épreuve exige en outre une version de `dsoxlab` qui joue le
`setup.yaml` d'un lab `shell` : c'est lui qui monte le terrain (issue
dsoxlab #298). Avec une version antérieure, `dsoxlab run` rend un
répertoire de travail vide, et rien ne dit pourquoi.

La mission est dans `dsoxlab challenge`.
