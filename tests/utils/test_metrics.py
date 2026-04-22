from prometheus_client import Counter, Histogram

from src.utils import metrics


class TestCounters:
    def test_bot_messages_total_is_counter(self):
        assert isinstance(metrics.bot_messages_total, Counter)

    def test_llm_requests_total_is_counter(self):
        assert isinstance(metrics.llm_requests_total, Counter)

    def test_llm_status_codes_total_is_counter(self):
        assert isinstance(metrics.llm_status_codes_total, Counter)

    def test_redis_operations_total_is_counter(self):
        assert isinstance(metrics.redis_operations_total, Counter)

    def test_db_queries_total_is_counter(self):
        assert isinstance(metrics.db_queries_total, Counter)

    def test_counters_accept_expected_labels(self):
        metrics.bot_messages_total.labels(status="success").inc()
        metrics.llm_requests_total.labels(model="m", status="success").inc()
        metrics.llm_status_codes_total.labels(status_code="200", model="m").inc()
        metrics.redis_operations_total.labels(operation="add", status="ok").inc()
        metrics.db_queries_total.labels(operation="get", status="ok").inc()


class TestHistogram:
    def test_llm_request_duration_is_histogram(self):
        assert isinstance(metrics.llm_request_duration_seconds, Histogram)

    def test_histogram_observe(self):
        metrics.llm_request_duration_seconds.labels(model="m").observe(0.5)


class TestStartMetricsServer:
    def test_calls_prometheus_start(self, mocker):
        mock = mocker.patch("src.utils.metrics.start_http_server")
        metrics.start_metrics_server(9000)
        mock.assert_called_once_with(9000)
