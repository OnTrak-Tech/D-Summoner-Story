terraform {
  backend "s3" {
    bucket         = "d-summoner-story-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "d-summoner-story-terraform-locks"
    encrypt        = true
  }
}