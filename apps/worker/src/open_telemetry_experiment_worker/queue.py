from saq import Queue

from open_telemetry_experiment_worker.config import config

queue = Queue.from_url(config.REDIS_URL)
