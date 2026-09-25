# La configuration cible. L'AMI est deja passee a la nouvelle valeur : c'est la
# demande metier, elle n'est pas a discuter.
#
# Cinq `???` restent, et chacun decide d'un comportement que le plan revelera.

resource "random_integer" "suffixe" {
  min = 100
  max = 999

  # A completer.
  #
  # Sans quoi ce nombre ne change JAMAIS, et le nom du groupe non plus. Or le
  # nom doit changer a chaque generation : c'est ce qui evite que l'ancienne et
  # la nouvelle grappe se disputent le meme.
  #
  # De quoi ce suffixe doit-il dependre pour etre retire quand le template
  # change ?
  ??? 
}

resource "aws_launch_template" "socle" {
  name          = "socle-app"
  image_id      = "ami-0000000000000b7"
  instance_type = "t3.micro"
}

resource "aws_autoscaling_group" "grappe" {
  # A completer : la nouvelle convention de nommage.
  ??? 

  min_size           = 2
  max_size           = 4
  desired_capacity   = 2
  availability_zones = ["eu-west-3a"]

  launch_template {
    id = aws_launch_template.socle.id

    # A completer.
    #
    # `"$Latest"` est le reflexe, et c'est un piege : cette chaine est CONNUE
    # au moment du plan, donc l'ASG ne bouge pas. Le groupe ne sera jamais
    # rafraichi, et personne ne s'en apercevra avant longtemps.
    #
    # Omettre l'argument ne vaut pas mieux : il retombe alors sur `"$Default"`,
    # avec le meme effet.
    #
    # Ce qu'il faut est une valeur CALCULEE a l'apply, donc inconnue au plan.
    version = ???
  }

  # A completer : le bloc qui decide de l'ORDRE du remplacement.
  #
  # Par defaut, Terraform detruit puis recree. Sur un groupe en service, cela
  # ouvre une fenetre a zero instance.
  ??? 

  instance_refresh {
    strategy = "Rolling"

    preferences {
      # A completer : les deux garde-fous de la bascule.
      #
      # L'un empeche de descendre sous la capacite cible, l'autre autorise a la
      # depasser le temps du remplacement. Sans le second, le premier ne peut
      # pas etre tenu : il faut bien de la place pour demarrer la nouvelle
      # instance avant d'arreter l'ancienne.
      ??? 
      ??? 
    }
  }
}
