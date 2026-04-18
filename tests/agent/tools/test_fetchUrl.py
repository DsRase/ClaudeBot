import httpx
import pytest

from src.agent.tools.fetch.fetchUrl import _extract_text, fetch_url


class TestExtractText:
    """Сценарии вычистки HTML."""

    def test_strips_script_and_style(self):
        """script/style/nav вычищаются полностью."""
        html = "<html><body><script>x=1</script>main<style>a{}</style></body></html>"
        assert _extract_text(html) == "main"

    def test_collapses_whitespace(self):
        """Пустые строки выкидываются, остальные тримятся."""
        html = "<html><body><p>  один  </p><p></p><p>два</p></body></html>"
        assert _extract_text(html) == "один\nдва"


def _mock_response(text: str, status_code: int = 200):
    return httpx.Response(status_code=status_code, text=text, request=httpx.Request("GET", "http://x"))


class TestFetchUrl:
    """Сценарии скачивания и парсинга страниц."""

    @pytest.mark.asyncio
    async def test_returns_extracted_text(self, mocker, monkeypatch):
        """Текст из HTML отдаётся очищенным от тэгов."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
        mocker.patch(
            "httpx.AsyncClient.get",
            new=mocker.AsyncMock(return_value=_mock_response("<p>hello</p>")),
        )

        result = await fetch_url("http://example.com")

        assert result == "hello"

    @pytest.mark.asyncio
    async def test_truncates_to_settings_limit(self, mocker, monkeypatch):
        """Длинный текст обрезается до Settings.fetch_max_content_chars символов."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
        from src.config import get_settings
        get_settings.cache_clear()
        limit = get_settings().fetch_max_content_chars
        big = "<p>" + ("a" * (limit + 5000)) + "</p>"
        mocker.patch(
            "httpx.AsyncClient.get",
            new=mocker.AsyncMock(return_value=_mock_response(big)),
        )

        result = await fetch_url("http://example.com")

        assert len(result) == limit, f"ожидалась обрезка до {limit}, получили {len(result)}"

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self, mocker, monkeypatch):
        """HTTP-ошибки пробрасываются (raise_for_status)."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
        mocker.patch(
            "httpx.AsyncClient.get",
            new=mocker.AsyncMock(return_value=_mock_response("nope", status_code=500)),
        )

        with pytest.raises(httpx.HTTPStatusError):
            await fetch_url("http://example.com")
