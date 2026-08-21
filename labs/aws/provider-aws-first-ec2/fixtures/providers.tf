# Ce bloc ne sait qu'une chose : la region.
#
# Tel quel, le provider appelle le vrai AWS, cherche des identifiants qu'il ne
# trouvera pas, et le plan echoue avant d'avoir rien planifie. A completer.
provider "aws" {
  region = var.aws_region
}
