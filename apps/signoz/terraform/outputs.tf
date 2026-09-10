output "dashboard_ids" {
  description = "Ids of signoz dashboards"
  value = {
    saq_worker_queue = signoz_dashboard.saq_worker_queue.id
    http_red         = signoz_dashboard.http_red.id
  }
}
