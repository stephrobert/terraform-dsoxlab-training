# Demande metier

La nouvelle AMI `ami-0000000000000b7` doit etre deployee sur la grappe
`grappe-app-742`, deja en service.

Deux exigences, et elles ne sont pas negociables :

1. **La capacite cible ne doit JAMAIS descendre**, pas une seconde. Le service
   tourne, et deux instances sont le minimum pour absorber le trafic.

2. **La nouvelle convention de nommage s'applique** : le nom du groupe doit
   porter un suffixe qui change a chaque generation. Deux generations ne
   doivent jamais pouvoir porter le meme nom.

Le socle est deja en place. Vous ne l'appliquez pas : vous produisez le PLAN qui
le ferait, et vous prouvez qu'il fait ce qu'on demande.
