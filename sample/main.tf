terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.33.0"
    }
  }
}

provider "aws" {
  # Configuration options
  region  = "ap-south-1" #Can be defined as a var
  profile = "default"
}

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
  availability_zone = "ap-south-1a" # Corrected to match provider region
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

resource "aws_instance" "ec2_nginx" {
  ami = "ami-0f5ee92e2d63a033e" # Amazon Linux 2 AMI for ap-south-1
  associate_public_ip_address = true
  instance_type = "t2.micro" # Uncommented and set to a valid instance type
  subnet_id = aws_subnet.subnet_oregon.id
  vpc_security_group_ids = [ aws_security_group.SG_Nginx.id ]
  root_block_device {
    delete_on_termination = true #to delete ebs volume when the instance is deleted
    volume_size = "10"
    volume_type = "gp2"
    tags = merge(local.common_tags,
    {
      Name = "Resource_EC2_EBS_Volume"
    }
    )
  }
  tags = merge(local.common_tags,
    {
      Name = "Resource_EC2_Nginx"
    }
    )
    lifecycle {
      create_before_destroy = true
    }
}

#Security group
resource "aws_security_group" "SG_Nginx" {
  description = "SG that allows port 443 & 80"
  name = "SG-Public"
  vpc_id = aws_vpc.vpc_oregon.id
    tags = merge(local.common_tags,
    {
      Name = "Resource_EC2_Nginx-SG"
    }
    )
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  description = "Allows port 80"
  security_group_id = aws_security_group.SG_Nginx.id # Uncommented and fixed
  from_port = 80
  to_port = 80
  ip_protocol = "tcp"
  cidr_ipv4 = "0.0.0.0/0"
  tags = {
    Name = "Rule-80"
  }
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  description = "Allows port 443"
  security_group_id = aws_security_group.SG_Nginx.id
  from_port = 443
  to_port = 443
  ip_protocol = "tcp"
  cidr_ipv4 = "0.0.0.0/0"
  tags = {
    Name = "Rule-443"
  }
}
