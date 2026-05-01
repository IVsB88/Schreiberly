import requests

_CONTEXT_DESCRIPTIONS = {
    "teams": "Teams-Nachricht — locker aber professionell. Natürliches Deutsch. Kurz halten.",
    "outlook": "E-Mail in Outlook — formeller Register. Vollständige Sätze. Passende Grußformel.",
    "jira": "Jira-Ticket — prägnant, handlungsorientiert, kein Fülltext. Max. 3 Sätze.",
    "miro": "Miro-Board — kurzer Haftnotizstil. Direkt. Umgangssprachlich ok.",
    "default": "Allgemeiner Text — Grammatik und Formulierungen korrigieren. Register und Länge beibehalten.",
}

_SYSTEM_TEMPLATE = (
    "Du bist ein professioneller Lektor für Deutsch als Fremdsprache.\n"
    "Kontext: {context_description}\n"
    "Aufgabe: Korrigiere den folgenden Text. Behalte die ursprüngliche Bedeutung.\n"
    "Korrigiere: Grammatik, Satzbau, Groß-/Kleinschreibung, Kommasetzung.\n"
    "Passe an: Register und Stil für den angegebenen Kontext.\n"
    "Antworte NUR mit dem korrigierten Text. Keine Erklärungen."
)

_PREAMBLE_STARTERS = ("hier ist", "natürlich", "gerne", "der korrigierte text")


def build_prompt(context: str, text: str) -> str:
    desc = _CONTEXT_DESCRIPTIONS.get(context, _CONTEXT_DESCRIPTIONS["default"])
    system = _SYSTEM_TEMPLATE.format(context_description=desc)
    return f"{system}\n\nText:\n{text}"


def strip_preamble(text: str) -> str:
    stripped = text.lstrip()
    lowered = stripped.lower()
    for starter in _PREAMBLE_STARTERS:
        if lowered.startswith(starter):
            for i, ch in enumerate(stripped):
                if ch in (":", "\n"):
                    return stripped[i + 1 :].lstrip()
            break
    return text


def call_ollama(
    session: requests.Session,
    endpoint: str,
    model: str,
    context: str,
    text: str,
    timeout: int,
) -> str:
    prompt = build_prompt(context, text)
    response = session.post(
        endpoint,
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["response"].strip()
