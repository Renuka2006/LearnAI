resource "aws_instance" "ec2_nginx" {
  ami = "ami-08c7263b3c75ca130" #Nginx AMI referred from AWS console 
  associate_public_ip_address = true
  #instance_type = "t2.micro"
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
  security_group_id = aws_security_group.SG_Nginx.id
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