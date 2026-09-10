resource "signoz_dashboard" "saq_worker_queue" {
  schema_version = "v6"
  name           = "saq-worker-queue"
  tags = [
    { key = "app", value = "worker" },
    { key = "managed-by", value = "terraform" },
  ]

  spec = {
    display = {
      name        = "SAQ Worker Queue"
      description = "Health of the SAQ job queue and workers, from the worker's OpenTelemetry metrics."
    }
    links     = []
    variables = []

    panels = {
      # Job throughput by status
      "11111111-1111-4111-8111-111111111111" = {
        kind = "Panel"
        spec = {
          display = { name = "Job Throughput (by status)" }
          links   = []
          plugin = {
            time_series_panel = {
              kind = "signoz/TimeSeriesPanel"
              spec = {
                visualization = { time_preference = "global_time", fill_spans = false }
                formatting    = { unit = "cps", decimal_precision = "2" }
                legend        = { position = "bottom", mode = "list" }
              }
            }
          }
          queries = [{
            kind = "time_series"
            spec = {
              name = "A"
              plugin = {
                builder_query = {
                  kind = "signoz/BuilderQuery"
                  spec = {
                    metrics = {
                      name          = "A"
                      step_interval = "60"
                      signal        = "metrics"
                      aggregations  = [{ metric_name = "saq.jobs", time_aggregation = "rate", space_aggregation = "sum", reduce_to = "sum" }]
                      filter        = { expression = "" }
                      group_by      = [{ name = "status", field_context = "attribute", field_data_type = "string" }]
                      having        = { expression = "" }
                      legend        = "{{status}}"
                    }
                  }
                }
              }
            }
          }]
        }
      }

      # Job processing duration p99 / p50
      "22222222-2222-4222-8222-222222222222" = {
        kind = "Panel"
        spec = {
          display = { name = "Job Processing Duration" }
          links   = []
          plugin = {
            time_series_panel = {
              kind = "signoz/TimeSeriesPanel"
              spec = {
                visualization = { time_preference = "global_time", fill_spans = false }
                formatting    = { unit = "s", decimal_precision = "2" }
                legend        = { position = "bottom", mode = "list" }
              }
            }
          }
          queries = [
            {
              kind = "time_series"
              spec = {
                name = "A"
                plugin = {
                  builder_query = {
                    kind = "signoz/BuilderQuery"
                    spec = {
                      metrics = {
                        name          = "A"
                        step_interval = "60"
                        signal        = "metrics"
                        aggregations = [
                          { metric_name = "saq.job.duration.bucket", time_aggregation = "rate", space_aggregation = "p99", reduce_to = "avg" },
                          { metric_name = "saq.job.duration.bucket", time_aggregation = "rate", space_aggregation = "p50", reduce_to = "avg" },
                        ]
                        filter = { expression = "" }
                        having = { expression = "" }
                        legend = ""
                      }
                    }
                  }
                }
              }
            },
          ]
        }
      }

      # Queue wait before processing (p99)
      "33333333-3333-4333-8333-333333333333" = {
        kind = "Panel"
        spec = {
          display = { name = "Queue Wait Before Processing (p99)" }
          links   = []
          plugin = {
            time_series_panel = {
              kind = "signoz/TimeSeriesPanel"
              spec = {
                visualization = { time_preference = "global_time", fill_spans = false }
                formatting    = { unit = "s", decimal_precision = "2" }
                legend        = { position = "bottom", mode = "list" }
              }
            }
          }
          queries = [{
            kind = "time_series"
            spec = {
              name = "A"
              plugin = {
                builder_query = {
                  kind = "signoz/BuilderQuery"
                  spec = {
                    metrics = {
                      name          = "A"
                      step_interval = "60"
                      signal        = "metrics"
                      aggregations  = [{ metric_name = "saq.job.wait.bucket", time_aggregation = "rate", space_aggregation = "p99", reduce_to = "avg" }]
                      filter        = { expression = "" }
                      having        = { expression = "" }
                      legend        = "p99 wait"
                    }
                  }
                }
              }
            }
          }]
        }
      }

      # Queue depth by state
      "44444444-4444-4444-8444-444444444444" = {
        kind = "Panel"
        spec = {
          display = { name = "Queue Depth (by state)" }
          links   = []
          plugin = {
            time_series_panel = {
              kind = "signoz/TimeSeriesPanel"
              spec = {
                visualization = { time_preference = "global_time", fill_spans = false }
                formatting    = { unit = "short", decimal_precision = "0" }
                legend        = { position = "bottom", mode = "list" }
              }
            }
          }
          queries = [{
            kind = "time_series"
            spec = {
              name = "A"
              plugin = {
                builder_query = {
                  kind = "signoz/BuilderQuery"
                  spec = {
                    metrics = {
                      name          = "A"
                      step_interval = "60"
                      signal        = "metrics"
                      aggregations  = [{ metric_name = "saq.queue.depth", time_aggregation = "avg", space_aggregation = "sum", reduce_to = "avg" }]
                      filter        = { expression = "" }
                      group_by      = [{ name = "state", field_context = "attribute", field_data_type = "string" }]
                      having        = { expression = "" }
                      legend        = "{{state}}"
                    }
                  }
                }
              }
            }
          }]
        }
      }

      # Live workers (single stat)
      "55555555-5555-4555-8555-555555555555" = {
        kind = "Panel"
        spec = {
          display = { name = "Live Workers" }
          links   = []
          plugin = {
            number_panel = {
              kind = "signoz/NumberPanel"
              spec = {
                visualization = { time_preference = "global_time" }
                formatting    = { unit = "short", decimal_precision = "0" }
              }
            }
          }
          queries = [{
            kind = "scalar"
            spec = {
              name = "A"
              plugin = {
                builder_query = {
                  kind = "signoz/BuilderQuery"
                  spec = {
                    metrics = {
                      name          = "A"
                      step_interval = "60"
                      signal        = "metrics"
                      aggregations  = [{ metric_name = "saq.queue.workers", time_aggregation = "avg", space_aggregation = "sum", reduce_to = "last" }]
                      filter        = { expression = "" }
                      having        = { expression = "" }
                      legend        = "workers"
                    }
                  }
                }
              }
            }
          }]
        }
      }

      # Job attempts (retry pressure)
      "66666666-6666-4666-8666-666666666666" = {
        kind = "Panel"
        spec = {
          display = { name = "Job Attempts (by status)" }
          links   = []
          plugin = {
            time_series_panel = {
              kind = "signoz/TimeSeriesPanel"
              spec = {
                visualization = { time_preference = "global_time", fill_spans = false }
                formatting    = { unit = "cps", decimal_precision = "2" }
                legend        = { position = "bottom", mode = "list" }
              }
            }
          }
          queries = [{
            kind = "time_series"
            spec = {
              name = "A"
              plugin = {
                builder_query = {
                  kind = "signoz/BuilderQuery"
                  spec = {
                    metrics = {
                      name          = "A"
                      step_interval = "60"
                      signal        = "metrics"
                      aggregations  = [{ metric_name = "saq.job.attempts", time_aggregation = "rate", space_aggregation = "sum", reduce_to = "sum" }]
                      filter        = { expression = "" }
                      group_by      = [{ name = "status", field_context = "attribute", field_data_type = "string" }]
                      having        = { expression = "" }
                      legend        = "{{status}}"
                    }
                  }
                }
              }
            }
          }]
        }
      }
    }

    layouts = [{
      grid = {
        kind = "Grid"
        spec = {
          display = { title = "Overview", collapse = { open = true } }
          items = [
            { x = 0, y = 0, width = 6, height = 6, content = { ref = "#/spec/panels/11111111-1111-4111-8111-111111111111" } },
            { x = 6, y = 0, width = 6, height = 6, content = { ref = "#/spec/panels/22222222-2222-4222-8222-222222222222" } },
            { x = 0, y = 6, width = 6, height = 6, content = { ref = "#/spec/panels/33333333-3333-4333-8333-333333333333" } },
            { x = 6, y = 6, width = 6, height = 6, content = { ref = "#/spec/panels/44444444-4444-4444-8444-444444444444" } },
            { x = 0, y = 12, width = 4, height = 6, content = { ref = "#/spec/panels/55555555-5555-4555-8555-555555555555" } },
            { x = 4, y = 12, width = 8, height = 6, content = { ref = "#/spec/panels/66666666-6666-4666-8666-666666666666" } },
          ]
        }
      }
    }]
  }
}
resource "signoz_dashboard" "http_red" {
  schema_version = "v6"
  name           = "http-red-services"
  tags = [
    { key = "app", value = "services" },
    { key = "managed-by", value = "terraform" },
  ]

  spec = {
    display = {
      name        = "HTTP RED (Services)"
      description = "Rate / Errors / Duration for the FastAPI services, derived from server spans."
    }
    links     = []
    variables = []

    panels = {
      # Request rate by service + endpoint
      "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa" = {
        kind = "Panel"
        spec = {
          display = { name = "Request Rate (by service & endpoint)" }
          links   = []
          plugin = {
            time_series_panel = {
              kind = "signoz/TimeSeriesPanel"
              spec = {
                visualization = { time_preference = "global_time", fill_spans = false }
                formatting    = { unit = "cps", decimal_precision = "2" }
                legend        = { position = "bottom", mode = "list" }
              }
            }
          }
          queries = [{
            kind = "time_series"
            spec = {
              name = "A"
              plugin = {
                builder_query = {
                  kind = "signoz/BuilderQuery"
                  spec = {
                    traces = {
                      name          = "A"
                      step_interval = "60"
                      signal        = "traces"
                      aggregations  = [{ expression = "rate()" }]
                      filter        = { expression = "http.route EXISTS AND http.route NOT IN ['/health', '/api/health']" }
                      group_by = [
                        { name = "service.name", field_context = "resource", field_data_type = "string" },
                        { name = "http.route", field_context = "attribute", field_data_type = "string" },
                      ]
                      having = { expression = "" }
                      legend = "{{service.name}} {{http.route}}"
                    }
                  }
                }
              }
            }
          }]
        }
      }

      # Latency p99 by endpoint
      "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb" = {
        kind = "Panel"
        spec = {
          display = { name = "Latency p99 (by endpoint)" }
          links   = []
          plugin = {
            time_series_panel = {
              kind = "signoz/TimeSeriesPanel"
              spec = {
                visualization = { time_preference = "global_time", fill_spans = false }
                formatting    = { unit = "ns", decimal_precision = "2" }
                legend        = { position = "bottom", mode = "list" }
              }
            }
          }
          queries = [{
            kind = "time_series"
            spec = {
              name = "A"
              plugin = {
                builder_query = {
                  kind = "signoz/BuilderQuery"
                  spec = {
                    traces = {
                      name          = "A"
                      step_interval = "60"
                      signal        = "traces"
                      aggregations  = [{ expression = "p99(duration_nano)" }]
                      filter        = { expression = "http.route EXISTS AND http.route NOT IN ['/health', '/api/health']" }
                      group_by = [
                        { name = "service.name", field_context = "resource", field_data_type = "string" },
                        { name = "http.route", field_context = "attribute", field_data_type = "string" },
                      ]
                      having = { expression = "" }
                      legend = "{{service.name}} {{http.route}}"
                    }
                  }
                }
              }
            }
          }]
        }
      }

      # 5xx error rate by endpoint
      "cccccccc-cccc-4ccc-8ccc-cccccccccccc" = {
        kind = "Panel"
        spec = {
          display = { name = "5xx Error Rate (by endpoint)" }
          links   = []
          plugin = {
            time_series_panel = {
              kind = "signoz/TimeSeriesPanel"
              spec = {
                visualization = { time_preference = "global_time", fill_spans = false }
                formatting    = { unit = "cps", decimal_precision = "2" }
                legend        = { position = "bottom", mode = "list" }
              }
            }
          }
          queries = [{
            kind = "time_series"
            spec = {
              name = "A"
              plugin = {
                builder_query = {
                  kind = "signoz/BuilderQuery"
                  spec = {
                    traces = {
                      name          = "A"
                      step_interval = "60"
                      signal        = "traces"
                      aggregations  = [{ expression = "rate()" }]
                      filter        = { expression = "http.route EXISTS AND http.route NOT IN ['/health', '/api/health'] AND http.response.status_code >= 500" }
                      group_by = [
                        { name = "service.name", field_context = "resource", field_data_type = "string" },
                        { name = "http.route", field_context = "attribute", field_data_type = "string" },
                      ]
                      having = { expression = "" }
                      legend = "{{service.name}} {{http.route}}"
                    }
                  }
                }
              }
            }
          }]
        }
      }
    }

    layouts = [{
      grid = {
        kind = "Grid"
        spec = {
          display = { title = "Overview", collapse = { open = true } }
          items = [
            { x = 0, y = 0, width = 6, height = 6, content = { ref = "#/spec/panels/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa" } },
            { x = 6, y = 0, width = 6, height = 6, content = { ref = "#/spec/panels/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb" } },
            { x = 0, y = 6, width = 12, height = 6, content = { ref = "#/spec/panels/cccccccc-cccc-4ccc-8ccc-cccccccccccc" } },
          ]
        }
      }
    }]
  }
}
