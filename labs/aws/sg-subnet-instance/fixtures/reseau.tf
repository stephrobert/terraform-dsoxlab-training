# Fourni, ne rien changer ici.
#
# DEUX subnets, et c'est deliberé : avec un seul, prendre « le premier » de la
# liste donnerait le bon resultat par accident, et le lab ne prouverait rien.
resource "aws_vpc" "lab" {
  cidr_block = var.vpc_cidr

  tags = {
    Name = "vpc-lab"
  }
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.lab.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, 1)

  tags = {
    Name = "subnet-public"
    Tier = "public"
  }
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.lab.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, 2)

  tags = {
    Name = "subnet-private"
    Tier = "private"
  }
}
