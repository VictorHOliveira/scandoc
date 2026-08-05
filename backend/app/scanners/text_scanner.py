import re

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


def scan_text(filename: str, data: bytes) -> dict:
    text = _decode(data)
    if _HTMLISH.search(text):
        from .html_scanner import scan_html

        return scan_html(filename, data)

    findings: list[dict] = []
    matches: list[str] = []
    hidden_parts: list[str] = []
    lines = text.splitlines()

    for idx, line in enumerate(lines):
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
    return {
        "format": "text",
        "findings": findings,
        "hidden_text": hidden_joined.strip(),
        "annotated_image": None,
        "injection_matches": sorted(set(matches)),
        "summary": {"lines": len(lines), "chars": len(text)},
    }
