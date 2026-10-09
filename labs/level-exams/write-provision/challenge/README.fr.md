# Épreuve de niveau A : écrire et provisionner un environnement de démonstration

Une équipe produit a besoin d'un environnement de démonstration sur l'hôte
libvirt de l'équipe : un réseau isolé et quelques machines, décrites par un
**catalogue**. Rien n'existe encore : vous écrivez le code Terraform, à la
racine de votre répertoire de travail, et vous le déployez.

Durée indicative : **45 minutes**. Aucun indice n'est proposé.

## Ce que vous recevez

- `entrees.auto.tfvars.json` : le préfixe de tout ce que vous créez, la plage
  du réseau, l'image cloud de base et le chemin de la clé publique de
  l'exploitation ;
- `catalogue.auto.tfvars.json` : le catalogue, sous la variable `machines`.
  Chaque machine y porte un `role` (`front`, `app` ou `db`), une `taille`
  (`petite` : 512 Mio, `moyenne` : 768 Mio) et une `generation` ;
- `acces/` : la clé de l'exploitation.

Ne modifiez pas ces fichiers : le harnais vous donnera d'autres catalogues et
observera ce que votre code en fait.

## Ce qui est attendu

Des résultats, vérifiés sur l'état réel des machines et des plans, jamais sur
la forme de votre code :

- **L'environnement existe.** Un réseau **isolé**, dont le nom commence par le
  préfixe, et, pour chaque entrée du catalogue, une machine dont le nom
  commence par `<préfixe>-<nom>`, à la taille demandée, raccordée à ce réseau,
  qui **démarre** réellement. Chaque machine accepte le compte `exploit` avec
  la clé de `acces/`, avec sudo sans mot de passe.
- **La configuration converge.** Après votre déploiement, un nouveau plan ne
  propose plus rien.
- **Le catalogue pilote tout.** Un catalogue invalide (taille ou rôle inconnu,
  champ manquant) est **refusé avant tout plan**. Retirer une entrée du
  catalogue détruit **cette machine seule**, sans toucher aux autres.
- **Une nouvelle génération remplace la machine.** Quand la `generation`
  d'une entrée change, sa machine est remplacée.
- **La machine `db` est critique.** Aucun plan ne peut la détruire ni la
  remplacer. Toute autre machine remplacée est **créée avant** que l'ancienne
  soit détruite.
- **Le secret de l'application arrive à destination, et nulle part ailleurs.**
  Chaque machine de rôle `app` reçoit un secret d'au moins 16 caractères dans
  `/etc/app/secret`, propriété de root, droits 600. Ce secret ne figure **ni
  dans le state ni dans aucun plan**.
- **Les versions des providers sont verrouillées**, et le verrou est conservé
  dans le répertoire de travail.

## Comment c'est noté

Le rapport donne un verdict par compétence : `workflow`, `resource`,
`parameterize`, `expression`, `guard`, `sensitive`. Une compétence en échec
renvoie aux leçons qui l'enseignent.

Pour faire noter : `dsoxlab check`.
