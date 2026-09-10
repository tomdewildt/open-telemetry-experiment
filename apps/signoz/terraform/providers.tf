terraform {
  required_version = ">= 1.6"

  required_providers {
    signoz = {
      source  = "SigNoz/signoz"
      version = "~> 0.1.4"
    }
  }
}

provider "signoz" {
  endpoint     = var.signoz_endpoint
  access_token = var.signoz_access_token
}
