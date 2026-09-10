variable "signoz_endpoint" {
  description = "Signoz endpoint"
  type        = string
  default     = "http://localhost:8080"
}

variable "signoz_access_token" {
  description = "Signoz access token"
  type        = string
  sensitive   = true
  default     = null
}
