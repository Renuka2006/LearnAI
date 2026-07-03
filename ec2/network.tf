#locals fn to declare commonly used params inside Terraform Project
locals {
  common_tags = {
    project = "Nginx_Server_deployment"
    #Name = "Resources_Nginx_Deployment"
  }
}

resource "aws_vpc" "vpc_oregon" {
  cidr_block = "10.0.0.0/16"
  tags = merge(local.common_tags,
    {
      Name = "Resource_VPC"
  })
}

resource "aws_subnet" "subnet_oregon" {
  vpc_id            = aws_vpc.vpc_oregon.id
  cidr_block        = "10.0.0.0/24"
  availability_zone = "us-west-2c"
  tags = merge(local.common_tags,
    {
      Name = "Resource_Subnet"
  })
}

resource "aws_internet_gateway" "igw_oregon" {
  vpc_id = aws_vpc.vpc_oregon.id
  tags = merge(local.common_tags,
    {
      Name = "Resource_IGW"
  })
}

resource "aws_route_table" "RT_oregon" {
  vpc_id = aws_vpc.vpc_oregon.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw_oregon.id
  }
  tags = merge(local.common_tags,
    {
      Name = "Resource_RT"
  })
}

resource "aws_route_table_association" "RT_Associate_oregon" {
  subnet_id      = aws_subnet.subnet_oregon.id
  route_table_id = aws_route_table.RT_oregon.id
}
