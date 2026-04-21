from prometheus_client import Counter, Histogram, start_http_server

bot_messages_total = Counter(
    "bot_messages_total",
    "Incoming Telegram messages",
    ["status"],  # triggered, ignored, no_access, success, error
)

llm_requests_total = Counter(
    "llm_requests_total",
    "LLM API calls",
    ["model", "status"],  # success, error
)

llm_status_codes_total = Counter(
    "llm_status_codes_total",
    "LLM API HTTP response status codes",
    ["status_code", "model"],
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM API call duration",
    ["model"],
    buckets=[1, 2, 5, 10, 20, 30, 60, 120],
)

redis_operations_total = Counter(
    "redis_operations_total",
    "Redis operations",
    ["operation", "status"],  # operation: add_message, get_context
)

db_queries_total = Counter(
    "db_queries_total",
    "SQLite queries",
    ["operation", "status"],
)


def start_metrics_server(port: int) -> None:
    start_http_server(port)
