# Demande de changement

Le service **api** doit rejoindre la plateforme.

Il doit apparaitre **entre `web` et `cache`** dans la liste `services`, pour
respecter l'ordre de demarrage documente par l'equipe.

Contrainte non negociable : les trois services deja en production (`web`,
`cache`, `db`) ne doivent **ni etre detruits ni etre recrees**. Leur identite
generee doit rester strictement identique.
