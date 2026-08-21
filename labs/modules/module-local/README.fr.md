# Un module local se lit sur place, il ne s'installe pas

Un module dont le `source` est un **chemin relatif** n'est pas installé : ses
fichiers sont déjà sur le disque, Terraform les lit **là où ils sont**. C'est ce
qui permet à plusieurs projets de partager un même module sans le dupliquer, et
c'est aussi ce qui rend inutile un réflexe très répandu, relancer `init` après
avoir modifié ce module.

Encore faut-il que Terraform considère votre chemin comme **local**. La règle est
stricte, et un chemin absolu n'y répond pas.

## Le terrain d'essai

Deux ateliers indépendants, un gabarit partagé :

```text
commun/gabarit/main.tf
atelier-nord/main.tf
atelier-sud/main.tf
```

Le gabarit produit une plaque à partir d'une étiquette :

```hcl
# commun/gabarit/main.tf
resource "local_file" "plaque" {
  filename = "${path.root}/plaques/${var.etiquette}.txt"
  content  = "plaque ${var.etiquette}\n"
}
```

Chaque atelier l'appelle par un **chemin relatif**, avec sa propre étiquette :

```hcl
module "gabarit" {
  source = "../commun/gabarit"

  etiquette = "nord"
}
```

## Ce que l'`init` fait, et ne fait pas

Il **enregistre** le module, il ne le copie pas :

```text
Initializing modules...
- gabarit in ../commun/gabarit
```

La preuve tient dans le répertoire de travail. Après `init`, `.terraform/modules/`
ne contient **qu'un seul fichier** :

```bash
ls -A .terraform/modules/
```

```text
modules.json
```

Aucun dossier. Ce `modules.json`, écrit par Terraform, dit où chaque module a été
trouvé :

```json
[
  {
    "Key": "gabarit",
    "Source": "../commun/gabarit",
    "Dir": "../commun/gabarit"
  }
]
```

`Source` est ce que vous avez écrit, `Dir` est l'endroit que Terraform lira. Pour
un chemin relatif, **les deux coïncident**, et pointent hors du cache. La
documentation le formule ainsi : « Local paths are special in that they are not
"installed" in the same sense that other sources are: the files are already
present on local disk. »

## Un seul module, plusieurs projets

Le second atelier lit **exactement le même dossier**, avec sa propre étiquette et
son propre state :

```bash
cd atelier-sud && terraform apply
terraform output -raw plaque
```

```text
./plaques/sud.txt
```

Deux projets racine, deux states séparés, **un seul module** : c'est tout
l'intérêt du chemin relatif. Chacun consomme le gabarit à sa façon sans que
l'autre en sache rien.

## Le réflexe inutile : relancer `init`

Modifiez le gabarit, puis **sans relancer `init`**, replanifiez depuis un
atelier :

```hcl
content = "plaque ${var.etiquette} (revision 2)\n"
```

```text
  # module.gabarit.local_file.plaque must be replaced
      ~ content = <<-EOT # forces replacement
```

```bash
terraform plan -detailed-exitcode; echo $?
```

```text
2
```

Le changement est **vu immédiatement**. Il n'y a **aucun cache à invalider**
pour le contenu d'un module local : `init` ne relit que le champ `source`, et
c'est donc son changement, à lui seul, qui justifie de le relancer.

## La règle qui décide : `./` ou `../`

Terraform ne devine pas qu'un chemin est local, il le **reconnaît à son
préfixe**. La documentation est normative : « A local path **must** begin with
either `./` or `../` ». Oubliez-le, et le chemin part vers un tout autre
mécanisme :

```hcl
module "gabarit" {
  source = "commun/gabarit"
}
```

```text
Error: Invalid module source address

Terraform failed to determine your intended installation method for remote
module package "commun/gabarit".

If you intended this as a path relative to the current module, use
"./commun/gabarit" instead. The "./" prefix indicates that the address is a
```

Le message donne lui-même la correction. Sans préfixe, Terraform a cherché un
**paquet distant**.

## Le cas qui trompe : le chemin absolu

Un chemin absolu désigne pourtant bien un dossier présent sur le disque. Terraform
ne le considère **pas** comme local pour autant : « Terraform does not consider an
absolute filesystem path to be a local path. Instead, Terraform will treat that in
a similar way as a remote module and copy it into the local module cache. »

L'`init` l'annonce sans ambiguïté :

```text
Downloading file:///chemin/vers/commun/gabarit for gabarit...
- gabarit in .terraform/modules/gabarit
```

Et le `modules.json` enregistre une tout autre chose :

```json
{
  "Key": "gabarit",
  "Source": "file:///chemin/vers/commun/gabarit",
  "Dir": ".terraform/modules/gabarit"
}
```

Une nuance mesurée sur 1.15.4, sous Linux : ce `Dir` est un **lien symbolique**
vers la source, pas la copie profonde que le mot « copy » laisse imaginer.

Deux conséquences pratiques. D'abord, votre configuration devient **non
portable** : le chemin absolu n'existe que sur votre machine. Ensuite, et c'est
le piège le plus coûteux, un module transformé en **paquet** ne peut plus
atteindre ce qui est **au-dessus de lui** : si ce module appelle lui-même un
voisin par `../autre`, l'`init` échoue.

```text
Error: Local module path escapes module package
```

## À vous de jouer

Vous savez qu'un module local n'est pas installé, que `modules.json` dit où
chaque appel lit vraiment, qu'une modification est vue sans `init`, que le
préfixe `./` ou `../` est ce qui définit un chemin local, et ce qu'un chemin
absolu change. Le challenge vous remet trois projets à brancher sur un même
module partagé, dont un qui doit servir de contre-exemple.

```bash
dsoxlab run modules-module-local
dsoxlab check modules-module-local
dsoxlab hint modules-module-local
```

Sous-objectif d'examen visé : **4b** (utiliser un module), niveau Associate.

Référence : [utiliser un module local](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/module-local/)
