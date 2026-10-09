# Épreuve de niveau B : exploiter le state

Cette épreuve clôt le niveau B de la formation Terraform. Ce n'est pas un
cours : elle mesure, sur un scénario neuf, quatre compétences travaillées dans
les modules State, Environnements et Automatiser.

| Compétence | Ce qui est vérifié |
| --- | --- |
| `state` | le verrou d'une autre exécution est attendu, jamais forcé ; une sauvegarde précède toute écriture |
| `refactor` | l'incident est réparé sans recréer aucune machine, plan de production à 0 |
| `environment` | `dev` et `prod` ont des states distincts ; un changement sur dev laisse prod intacte |
| `automate` | `chaine.sh` rend 0, 2 ou 1, ne pose jamais de question, applique le plan relu |

Prérequis du poste : Terraform 1.16, libvirt (`qemu:///system`) et Incus, comme
pour les labs de Premières infras. La préparation télécharge l'image cloud et le
stockage S3 la première fois, empreintes vérifiées.

Cette épreuve exige en outre une version de `dsoxlab` qui joue le
`setup.yaml` d'un lab `shell` : c'est lui qui monte le terrain (issue
dsoxlab #298). Avec une version antérieure, `dsoxlab run` rend un
répertoire de travail vide, et rien ne dit pourquoi.

La mission est dans `dsoxlab challenge`.
