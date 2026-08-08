import re
from typing import Callable, Optional

from . import injection_scanner, unicode_scanner
from .common import finding, snippet

_HTMLISH = re.compile(r"<(html|!doctype|head|body|div|p|span|style|script)\b", re.IGNORECASE)


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def scan_text(filename: str, data: bytes, on_progress: Callable[[int, str], None] | None = None) -> dict:
    if on_progress:
        on_progress(15, "Lendo conteúdo do texto")
    text = _decode(data)
    if _HTMLISH.search(text):
        from .html_scanner import scan_html

        return scan_html(filename, data, on_progress=on_progress)

    findings: list[dict] = []
    matches: list[str] = []
    hidden_parts: list[str] = []
    lines = text.splitlines()

    total = max(len(lines), 1)
    for idx, line in enumerate(lines):
        if idx % 200 == 0 and on_progress:
            on_progress(20 + int(50 * idx / total), "Analisando linhas do texto")
        if not line.strip():
            continue
        loc = f"linha {idx + 1}"
        for occ in unicode_scanner.find_invisible(line):
            findings.append(
                finding(
                    "high",
                    "zero_width",
                    "Caractere invisível encontrado",
                    f"'{occ['name']}' (U+{occ['index']:04X}) aparece {occ['count']}x no texto.",
                    loc,
                    snippet(line),
                )
            )
            hidden_parts.append(line)
        matches.extend(injection_scanner.scan_injection(line))
        for m in injection_scanner.scan_injection(line):
            findings.append(
                finding(
                    "medium",
                    "injection_visible",
                    "Frase de manipulação de IA encontrada",
                    "O texto contém padrão típico de prompt injection.",
                    loc,
                    m,
                )
            )

    hidden_joined = "\n".join(dict.fromkeys(hidden_parts))
    if on_progress:
        on_progress(90, "Finalizando análise")
    return {
        "format": "text",
        "findings": findings,
        "hidden_text": hidden_joined.strip(),
        "annotated_image": None,
        "injection_matches": sorted(set(matches)),
        "summary": {"lines": len(lines), "chars": len(text)},
    }
