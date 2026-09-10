output "dashboard_ids" {
  description = "IDs of the managed SigNoz dashboards"
  value = {
    saq_worker_queue = signoz_dashboard.saq_worker_queue.id
    http_red         = signoz_dashboard.http_red.id
  }
}
