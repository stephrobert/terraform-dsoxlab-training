# Réattester les labs de ce catalogue

> Page écrite le 2026-10-19, avec des valeurs **mesurées sur le disque** et non
> recopiées. Les chiffres vieillissent : le `validation-labs.json` reste la
> source de vérité pour les verdicts.

## Pourquoi cette page existe

Le 2026-10-19, une campagne de réattestation a inscrit **douze faux ROUGE** dans
un catalogue avant d'être arrêtée, et s'est bloquée vingt-trois minutes dans un
autre. Aucune des deux causes ne tenait aux labs : un `.venv` dont les shebangs
désignaient l'ancien nom du dépôt après son renommage, et un outil en ligne de
commande qui attendait un réseau que le bac à sable ne lui donnait pas.

Dans les deux cas, le validateur **avait l'air de mesurer les labs alors qu'il
mesurait sa propre panne**, et il l'écrivait dans le relevé. Un faux ROUGE coûte
plus cher qu'une absence de verdict : il envoie chercher un défaut dans un lab
qui n'en a pas.

## Ce que ce catalogue exige

- **dsoxlab 0.5.4 ou plus** dans le `PATH`. C'est la version du moteur qui sera inscrite dans le relevé, et le relevé la déclare pour TOUS les labs : voir la section sur le rejeu partiel.
- **`.vault-pass` à la racine** : 327 fichier(s) de solution de ce catalogue sont chiffrés par ansible-vault, et le cycle les pose déchiffrés. Le secret n'est jamais commité. Ici : présent.
- **Docker joignable** : 11 lab(s) déclarent `runtime.services`. Un service injoignable fait échouer `run` et `check`, qui ne notent pas un 0 silencieux.

### Attention : « shell » ne veut pas dire « sans hyperviseur »

Les 91 labs de ce catalogue sont en `runtime: shell`, donc `dsoxlab provision`
n'y est jamais appelé. Mais **six d'entre eux provisionnent leurs propres
machines** par le provider libvirt, parce que c'est précisément leur sujet :
`first-infra/first-infrastructure`, `first-infra/virtual-network`,
`first-infra/vm-libvirt`, `level-exams/modularize`,
`level-exams/operate-state` et `level-exams/write-provision`.

Mesuré en regardant tourner la campagne : quatre domaines `tfx18735-*` sont
apparus dans `virsh list` pendant qu'elle avançait. Conséquence pratique, une
campagne sur ce catalogue a besoin d'un hyperviseur joignable et de mémoire
libre, et elle ne doit pas tourner en même temps qu'une campagne sur un
catalogue à labs `vm` : les deux se disputeraient la RAM, et les échecs par
épuisement ressemblent à des défauts de lab.

Onze autres labs déclarent `runtime.services`, donc des conteneurs locaux,
qui demandent Docker mais pas l'hyperviseur.

## La commande

```bash
uv run scripts/valider-labs.py
```

Un seul lab, pour éprouver le harnais avant d'engager les 91 :

```bash
uv run scripts/valider-labs.py --lab <id-du-lab>
```

**Commencer par un seul lab n'est pas une précaution de principe.** C'est ce qui
distingue un défaut d'environnement d'un défaut de lab : si le lab unitaire
passe, le harnais est sain ; s'il échoue comme les autres, c'est le harnais
qu'il faut réparer.

## L'état actuel

Relevé actuel : 91 VALIDE. Moteur déclaré : dsoxlab 0.5.4. Les verdicts ne portent **aucune date individuelle**. Durée cumulée du dernier cycle mesuré : **28 minutes** pour 91 labs, hors provisionnement et destruction d'infrastructure.

## Les quatre pièges qui produisent un faux verdict

**1. Un `.venv` au shebang mort.** Si le dépôt a été renommé, les scripts de
`.venv/bin/` pointent encore l'ancien chemin et ne s'exécutent plus. Le
symptôme est un échec identique sur chaque lab, souvent sur le déchiffrement de
la solution. Vérification et correctif :

```bash
head -1 .venv/bin/ansible-vault      # le chemin doit exister
uv venv --clear && uv sync           # le recréer
```

**2. `uv run --no-sync` sur un venv vide.** Le drapeau suppose un environnement
déjà peuplé. Sur un clone neuf, il rend un `ModuleNotFoundError` avant d'avoir
regardé un seul lab. Lancer sans `--no-sync` la première fois.

**3. Un outil qui attend un réseau que le bac à sable ne donne pas.** Mesuré
sur un `octl --version` resté bloqué vingt-trois minutes : seule la commande de
premier niveau est exemptée, un sous-processus ne l'est pas. Si une campagne
n'avance plus, regarder ses processus enfants avant de soupçonner un lab :

```bash
ps -eo pid,etimes,cmd | grep -E 'python.*valider[-]labs'
ps --ppid <pid-du-validateur> -o pid,etimes,cmd
```

**4. Un rejeu partiel rend l'en-tête du relevé faux.** La version du moteur est
enregistrée **une fois pour tout le fichier**, alors que les verdicts sont
individuels. Rejouer un seul lab réécrit donc cet en-tête, et le relevé affirme
que tous ses labs ont été attestés avec la version courante. Soit on rejoue tout,
soit on restaure le relevé :

```bash
git checkout -- validation-labs.json
```

## Ce que le relevé ne dit pas

Il ne dit pas **avec quelle version du moteur chaque lab** a été attesté, mais
seulement celle de la dernière campagne. C'est un manque connu, et il se voit
dès qu'une campagne est partielle.

Ce catalogue enregistre bien cet en-tête (`genere_le`, `dsoxlab` et la version des outils employés), ce qui est la bonne pratique de la collection.

## Pourquoi les verdicts de ce catalogue sont périmés

Un **seul** commit les a périmés, et il est vérifié plutôt que repris d'une liste : `bb7ac57` du **2026-10-17**, « fix(labs): les messages d'échec en EN + FR, leurs accents, et deux labs qui notaient faux (#34) », qui touche **93 fichiers de tests**.

Ce n'est donc pas une dérive progressive : c'est une campagne coordonnée de bilinguisation des messages d'échec, menée le 2026-10-17 sur huit catalogues et 289 fichiers de tests. L'intitulé de ce commit nomme en outre un défaut corrigé au passage, et c'est lui qui rend le rejeu obligatoire : un test qui notait faux invalide le verdict qu'il a rendu.

À ne pas confondre avec le commit du 2026-10-19, qui a changé l'hôte des `doc_url` de `blog.` à `www.`. Celui-là touche des descripteurs et de la documentation, il ne change aucun geste et ne périme rien.

## Le format du relevé décide de ce que le site peut en dire

Le relevé de ce catalogue est au format **enveloppé**, et le site y lit bien la version du moteur, actuellement « dsoxlab 0.5.4 ».

Le générateur du site ne lit `genere_le` et `dsoxlab` **que si la clé `labs`
est un dictionnaire** : un relevé dont les clés de premier niveau sont
directement les identifiants de labs part dans une autre branche, qui rend une
date et un outil vides. Corriger le champ sans corriger le format ne servirait
donc à rien, et c'est pour ça que les deux sont dits ensemble ici.
