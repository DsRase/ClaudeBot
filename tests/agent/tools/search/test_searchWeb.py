import pytest

from src.agent.tools.search.searchWeb import search_web


class TestSearchWeb:
    """Сценарии вызова search_web."""

    @pytest.mark.asyncio
    async def test_returns_normalized_results(self, mocker, monkeypatch):
        """Поля DDGS (title/href/body) переименовываются в title/url/snippet."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        ddgs_instance = mocker.MagicMock()
        ddgs_instance.text.return_value = [
            {"title": "T1", "href": "http://a", "body": "S1"},
            {"title": "T2", "href": "http://b", "body": "S2"},
        ]
        mocker.patch("src.agent.tools.search.searchWeb.DDGS", return_value=ddgs_instance)

        results = await search_web("python", max_results=2)

        assert results == [
            {"title": "T1", "url": "http://a", "snippet": "S1"},
            {"title": "T2", "url": "http://b", "snippet": "S2"},
        ], "формат результатов не нормализован"

    @pytest.mark.asyncio
    async def test_uses_settings_default_when_max_results_none(self, mocker, monkeypatch):
        """Если max_results не задан, берётся дефолт из Settings."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        ddgs_instance = mocker.MagicMock()
        ddgs_instance.text.return_value = []
        mocker.patch("src.agent.tools.search.searchWeb.DDGS", return_value=ddgs_instance)
        from src.config import get_settings
        get_settings.cache_clear()

        await search_web("query")

        kwargs = ddgs_instance.text.call_args.kwargs
        assert kwargs["max_results"] == get_settings().search_default_max_results, \
            "не подставился дефолт из settings.search_default_max_results"

    @pytest.mark.asyncio
    async def test_runs_in_thread(self, mocker, monkeypatch):
        """Sync DDGS должен прогоняться через asyncio.to_thread, а не блокировать loop."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        mocker.patch("src.agent.tools.search.searchWeb.DDGS").return_value.text.return_value = []
        spy = mocker.patch("src.agent.tools.search.searchWeb.asyncio.to_thread", new=mocker.AsyncMock(return_value=[]))

        await search_web("python", max_results=3)

        spy.assert_awaited_once(), "search_web обязан звать asyncio.to_thread"

    @pytest.mark.asyncio
    async def test_missing_keys_default_to_empty(self, mocker, monkeypatch):
        """Если в результате DDGS нет какого-то поля — оно становится пустой строкой."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        ddgs_instance = mocker.MagicMock()
        ddgs_instance.text.return_value = [{"title": "T1"}]
        mocker.patch("src.agent.tools.search.searchWeb.DDGS", return_value=ddgs_instance)

        results = await search_web("q", max_results=1)

        assert results[0]["url"] == "" and results[0]["snippet"] == "", \
            "отсутствующие ключи должны заменяться пустой строкой"
