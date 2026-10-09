# Épreuve de niveau A : écrire et provisionner

Cette épreuve clôt le niveau A de la formation Terraform. Ce n'est pas un
cours : elle mesure, sur un scénario neuf, six compétences travaillées dans
les modules Découvrir, Écrire du code et Premières infras.

| Compétence | Ce qui est vérifié |
| --- | --- |
| `workflow` | après le déploiement, un plan ne propose plus rien |
| `resource` | chaque machine du catalogue existe, à sa taille, sur un réseau isolé, et démarre ; les providers sont verrouillés |
| `parameterize` | un catalogue invalide est refusé avant tout plan |
| `expression` | retirer une entrée du catalogue détruit cette machine seule |
| `guard` | la machine critique refuse destruction et remplacement ; une autre machine est recréée avant d'être détruite |
| `sensitive` | le secret d'application arrive dans la machine, et ne figure ni dans le state ni dans le plan |

Prérequis du poste : Terraform 1.16 et libvirt (`qemu:///system`), comme pour
les labs de Premières infras. La préparation télécharge l'image cloud la
première fois, empreinte vérifiée.

Cette épreuve exige en outre une version de `dsoxlab` qui joue le
`setup.yaml` d'un lab `shell` : c'est lui qui monte le terrain (issue
dsoxlab #298). Avec une version antérieure, `dsoxlab run` rend un
répertoire de travail vide, et rien ne dit pourquoi.

La mission est dans `dsoxlab challenge`.
