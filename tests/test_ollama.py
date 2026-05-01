import pytest
import requests
from unittest.mock import MagicMock

from schreibarrly.ollama import build_prompt, strip_preamble, call_ollama


class TestBuildPrompt:
    def test_contains_text(self):
        prompt = build_prompt("jira", "some text")
        assert "some text" in prompt

    def test_contains_system_instruction(self):
        prompt = build_prompt("default", "text")
        assert "Antworte NUR mit dem korrigierten Text" in prompt

    def test_jira_context_description(self):
        prompt = build_prompt("jira", "text")
        assert "Jira" in prompt

    def test_teams_context_description(self):
        prompt = build_prompt("teams", "text")
        assert "Teams" in prompt

    def test_outlook_context_description(self):
        prompt = build_prompt("outlook", "text")
        assert "Outlook" in prompt

    def test_unknown_context_falls_back_to_default(self):
        assert build_prompt("unknown_app", "text") == build_prompt("default", "text")

    @pytest.mark.parametrize("ctx", ["teams", "outlook", "jira", "miro", "default"])
    def test_all_contexts_include_text(self, ctx):
        assert "Testtext" in build_prompt(ctx, "Testtext")


class TestStripPreamble:
    def test_clean_text_unchanged(self):
        text = "Das ist der korrigierte Satz."
        assert strip_preamble(text) == text

    def test_strips_hier_ist_at_colon(self):
        assert strip_preamble("Hier ist der Text:\nErgebnis.") == "Ergebnis."

    def test_strips_natuerlich_at_colon(self):
        assert strip_preamble("Natürlich, hier ist der Text: Guten Tag.") == "Guten Tag."

    def test_strips_gerne_at_colon(self):
        assert strip_preamble("Gerne: Hier ist die Antwort.") == "Hier ist die Antwort."

    def test_strips_der_korrigierte_text_at_colon(self):
        assert strip_preamble("Der korrigierte Text:\nDas Ergebnis.") == "Das Ergebnis."

    def test_strips_at_newline_delimiter(self):
        assert strip_preamble("Hier ist\nDas Ergebnis.") == "Das Ergebnis."

    def test_no_delimiter_returns_original(self):
        text = "Hier ist der Text ohne Trennzeichen"
        assert strip_preamble(text) == text

    def test_leading_whitespace_in_text(self):
        assert strip_preamble("  Hier ist der Text:\nErgebnis.") == "Ergebnis."

    def test_empty_string(self):
        assert strip_preamble("") == ""

    def test_case_insensitive_matching(self):
        assert strip_preamble("HIER IST: Ergebnis.") == "Ergebnis."

    def test_strips_leading_whitespace_after_delimiter(self):
        assert strip_preamble("Gerne:   Satz.") == "Satz."


class TestCallOllama:
    def _mock_session(self, response_text: str) -> MagicMock:
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": response_text}
        session.post.return_value = mock_resp
        return session

    def test_returns_stripped_response(self):
        session = self._mock_session("  Corrected text.  ")
        result = call_ollama(session, "http://localhost:11434/api/generate", "mistral", "jira", "input", 30)
        assert result == "Corrected text."

    def test_posts_to_endpoint(self):
        session = self._mock_session("ok")
        call_ollama(session, "http://localhost:11434/api/generate", "mistral", "teams", "text", 30)
        url = session.post.call_args[0][0]
        assert url == "http://localhost:11434/api/generate"

    def test_payload_model(self):
        session = self._mock_session("ok")
        call_ollama(session, "http://localhost:11434/api/generate", "llama3.1", "default", "text", 30)
        payload = session.post.call_args[1]["json"]
        assert payload["model"] == "llama3.1"

    def test_payload_stream_false(self):
        session = self._mock_session("ok")
        call_ollama(session, "http://localhost:11434/api/generate", "mistral", "default", "text", 30)
        payload = session.post.call_args[1]["json"]
        assert payload["stream"] is False

    def test_payload_contains_text(self):
        session = self._mock_session("ok")
        call_ollama(session, "http://localhost:11434/api/generate", "mistral", "jira", "my jira text", 30)
        payload = session.post.call_args[1]["json"]
        assert "my jira text" in payload["prompt"]

    def test_timeout_passed(self):
        session = self._mock_session("ok")
        call_ollama(session, "http://localhost:11434/api/generate", "mistral", "default", "text", 60)
        assert session.post.call_args[1]["timeout"] == 60

    def test_propagates_connection_error(self):
        session = MagicMock()
        session.post.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(requests.exceptions.ConnectionError):
            call_ollama(session, "http://localhost:11434/api/generate", "mistral", "default", "text", 30)

    def test_propagates_timeout(self):
        session = MagicMock()
        session.post.side_effect = requests.exceptions.Timeout()
        with pytest.raises(requests.exceptions.Timeout):
            call_ollama(session, "http://localhost:11434/api/generate", "mistral", "default", "text", 30)
